#!/usr/bin/env python3
"""
chaturbate_scraper_updated.py

This module provides scraping functions for Chaturbate (and Stripchat) streams.
The updated Chaturbate scraper uses a POST request to retrieve the HLS URL 
via free proxies. SSL verification is disabled due to known proxy issues.
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
import types
import tempfile  # For generating unique user-data directories
import os
import re
import logging
import uuid
import time
import random
import requests
import urllib3
# --- Monkey Patch for blinker._saferef ---
if 'blinker._saferef' not in sys.modules:
    saferef = types.ModuleType('blinker._saferef')
    import weakref
    class SafeRef(weakref.ref):
        def __init__(self, ob, callback=None):
            super().__init__(ob, callback)
            self._hash = hash(ob)
        def __hash__(self):
            return self._hash
        def __eq__(self, other):
            try:
                return self() is other()
            except Exception:
                return False
    saferef.SafeRef = SafeRef
    sys.modules['blinker._saferef'] = saferef
# --- End of Monkey Patch ---
from requests.exceptions import RequestException, SSLError
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from flask import jsonify, current_app
from datetime import datetime
import threading

# Disable insecure request warnings due to disabled SSL certificate verification.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import models and database session for stream creation.
from models import Stream, ChaturbateStream, StripchatStream, Assignment, User
from extensions import db
from notifications import send_text_message

# Global dictionaries to hold job statuses.
scrape_jobs = {}
stream_creation_jobs = {}
executor = ThreadPoolExecutor(max_workers=1)  # Thread pool for parallel scraping

PROXY_LIST = []
PROXY_LIST_LAST_UPDATED = None
PROXY_LOCK = threading.Lock()
PROXY_UPDATE_INTERVAL = 3600  


def update_proxy_list():
    """Fetch fresh proxies from free API services"""
    try:
        # Try ProxyScrape API first
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            timeout=15
        )
        if response.status_code == 200 and response.text:
            proxies = [proxy.strip() for proxy in response.text.split('\n') if proxy.strip()]
            if len(proxies) > 20:  # Ensure we got enough proxies
                return proxies
                
        # Fallback to other sources
        response = requests.get(
            "https://www.proxy-list.download/api/v1/get?type=http",
            timeout=15
        )
        if response.status_code == 200 and response.text:
            proxies = [proxy.strip() for proxy in response.text.split('\n') if proxy.strip()]
            if len(proxies) > 20:
                return proxies
                
        # Return None if both failed
        return None
    except Exception as e:
        logging.error(f"Failed to update proxy list: {str(e)}")
        return None

def get_random_proxy() -> dict:
    """
    Select a random proxy from the proxy list, refreshing if needed.
    
    Returns:
        dict: A dictionary with HTTP and HTTPS proxies formatted for requests.
    """
    global PROXY_LIST, PROXY_LIST_LAST_UPDATED
    
    # Check if proxies need updating
    with PROXY_LOCK:
        current_time = time.time()
        if not PROXY_LIST or not PROXY_LIST_LAST_UPDATED or \
           current_time - PROXY_LIST_LAST_UPDATED > PROXY_UPDATE_INTERVAL:
            # Try different methods to get proxies
            new_proxies = update_proxy_list() or get_proxies_with_library() or scrape_free_proxy_list() # type: ignore
            
            if new_proxies and len(new_proxies) >= 10:
                PROXY_LIST = new_proxies
                PROXY_LIST_LAST_UPDATED = current_time
                logging.info(f"Updated proxy list with {len(PROXY_LIST)} proxies")
            elif not PROXY_LIST:
                # Fallback to original static list if we have no proxies at all
                PROXY_LIST = [
                    "52.67.10.183:80",
                    "200.250.131.218:80",
                    # ...rest of your static list
                ]
                logging.warning("Using static proxy list as fallback")
    
    # If we have proxies, select a random one
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
    else:
        # Return None if no proxies available
        return None

def create_selenium_driver_with_proxy(headless=True):
    """
    Create a Selenium driver configured with a random proxy
    
    Args:
        headless (bool): Whether to run the browser in headless mode
        
    Returns:
        webdriver: Configured Selenium Wire webdriver
    """
    from seleniumwire import webdriver
    from selenium.webdriver.chrome.options import Options
    import tempfile
    
    # Get a random proxy
    proxy_dict = get_random_proxy()
    if not proxy_dict:
        logging.warning("No proxies available, using direct connection")
        proxy_address = None
    else:
        # Extract the proxy address (remove http:// prefix)
        proxy_address = proxy_dict["http"].replace("http://", "")
    
    # Configure Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Anti-detection settings
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Create a unique user data directory
    unique_user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={unique_user_data_dir}")
    
    # Configure Selenium Wire options with proxy if available
    seleniumwire_options = {}
    if proxy_address:
        seleniumwire_options = {
            'proxy': {
                'http': f'http://{proxy_address}',
                'https': f'http://{proxy_address}',
                'verify_ssl': False,  # Disable SSL verification due to proxy issues
            }
        }
    
    # Initialize the driver
    driver = webdriver.Chrome(
        options=chrome_options,
        seleniumwire_options=seleniumwire_options
    )
    
    return driver


# --- Helper Functions for Job Progress ---
def update_job_progress(job_id, percent, message):
    """Update the progress of a scraping job"""
    now = time.time()
    if job_id not in scrape_jobs or 'start_time' not in scrape_jobs[job_id]:
        scrape_jobs[job_id] = {'start_time': now}
    elapsed = now - scrape_jobs[job_id]['start_time']
    estimated = None
    if percent > 0:
        estimated = (100 - percent) / percent * elapsed
    scrape_jobs[job_id].update({
        "progress": percent,
        "message": message,
        "elapsed": round(elapsed, 1),
        "estimated_time": round(estimated, 1) if estimated is not None else None,
    })
    logging.info("Job %s progress: %s%% - %s (Elapsed: %ss, Est: %ss)",
                 job_id, percent, message,
                 scrape_jobs[job_id]['elapsed'],
                 scrape_jobs[job_id]['estimated_time'])

def update_stream_job_progress(job_id, percent, message):
    """Update job progress with safe initialization"""
    now = time.time()
    
    # Initialize job with default values
    job = stream_creation_jobs.setdefault(job_id, {
        'start_time': now,
        'progress': 0,
        'message': '',
        'estimated_time': 0,
        'last_updated': now,
        'error': None,
        'stream': None
    })
    
    # Calculate time estimates
    elapsed = now - job['start_time']
    if percent > 0 and percent < 100:
        estimated_total = elapsed / (percent / 100)
        estimated_remaining = max(0, int(estimated_total - elapsed))
    else:
        estimated_remaining = 0

    # Update only if significant change
    if (abs(percent - job['progress']) > 1 or
        message != job['message'] or
        percent == 100):
        
        job.update({
            'progress': min(100, max(0, percent)),
            'message': message,
            'estimated_time': estimated_remaining,
            'last_updated': now
        })
        
        logging.info("Stream Job %s: %s%% - %s (Est: %ss)",
                    job_id, percent, message, estimated_remaining)

# --- New Helper Functions for Chaturbate Scraping ---
def extract_room_slug(url: str) -> str:
    """Extract the room slug from a Chaturbate URL"""
    parsed_url = urlparse(url)
    path_parts = [part for part in parsed_url.path.split('/') if part]
    if not path_parts:
        raise ValueError("No room slug found in URL")
    return path_parts[0]


def get_proxies_with_library(count=50):
    """Get working proxies using free-proxy library"""
    try:
        from fp.fp import FreeProxy
        
        proxies = []
        for _ in range(count):
            try:
                proxy = FreeProxy(timeout=1, https=True).get()
                if proxy:
                    # Convert from URL format to IP:PORT format
                    proxy = proxy.replace("http://", "").replace("https://", "")
                    proxies.append(proxy)
            except Exception:
                continue
                
        return proxies if proxies else None
    except ImportError:
        logging.error("free-proxy library not installed. Run: pip install free-proxy")
        return None
    except Exception as e:
        logging.error(f"Error getting proxies with library: {str(e)}")
        return None

def get_random_proxy() -> dict:
    """
    Select a random proxy from the proxy list.
    
    Returns:
        dict: A dictionary with HTTP and HTTPS proxies formatted for requests.
    """
    proxy = random.choice(PROXY_LIST)
    return {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }




def get_hls_url(room_slug: str, max_attempts: int = 15) -> dict:
    """
    Send a POST request to Chaturbate's endpoint to fetch the HLS URL for a given room.
    Includes necessary headers and cookies observed from browser DevTools.
    """
    url = 'https://chaturbate.com/get_edge_hls_url_ajax/'
    
    # Dynamic boundary generation
    boundary = uuid.uuid4().hex
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://chaturbate.com/{room_slug}/',
        'Origin': 'https://chaturbate.com',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Cookie': (
            'csrftoken=QBEfLYOhYb02QMAA8FsDhvimMi2rbhTh; '
            '__cf_bm=aRWJoCGvyxZsRyCS9qMJeMwF1ikmvIEucwTQpB3VDcE-1743303491-1.0.1.1-pc6j_3W8_POkMuCh2yhnhdG18vOaMl1tAsv9bIjj8wDQn9M4W3pGJN5yaucI8_vJp4meSVffE62zILQmuHg.ipapPlEw3OCsfsBNg05dEV0; '
            'sbr=sec:sbr9f095e3f-07ec-4e77-a51a-051c8118632f:1txykY:nZcRPVNiTcLgruuwAyCND2URhh7k8KiarIG-keMrJm0; '
            'agreeterms=1; '
            'stcki="Eg6Gdq=1"'
        )
    }

    # Construct dynamic multipart payload
    payload = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="room_slug"\r\n\r\n'
        f'{room_slug}\r\n'
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="bandwidth"\r\n\r\n'
        'high\r\n'
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="current_edge"\r\n\r\n'
        '\r\n'  # Empty current_edge to let server assign
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="exclude_edge"\r\n\r\n'
        '\r\n'
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n\r\n'
        'QBEfLYOhYb02QMAA8FsDhvimMi2rbhTh\r\n'
        f'--{boundary}--\r\n'
    )

    attempts = 0
    while attempts < max_attempts:
        proxy_dict = get_random_proxy()
        try:
            response = requests.post(
                url,
                headers=headers,
                data=payload.encode('utf-8'),
                proxies=proxy_dict,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            result = response.json()

            if result.get('room_status') == 'offline':
                return {'error': 'room_offline', 'message': 'Stream is offline'}

            hls_url = result.get("hls_url") or result.get("url")
            if hls_url:
                result["hls_url"] = hls_url
                return result
            
            attempts += 1
        except Exception as e:
            attempts += 1
            time.sleep(1)

    return None

def fetch_chaturbate_hls_with_curl_method(room_slug):
    """
    Direct implementation of the curl-based approach to fetch HLS URL.
    This serves as a backup method if other approaches fail.
    
    Args:
        room_slug (str): The Chaturbate room slug/username
    
    Returns:
        dict: Response containing HLS URL or error information
    """
    url = 'https://chaturbate.com/get_edge_hls_url_ajax/'
    boundary = f'geckoformboundary{uuid.uuid4().hex[:24]}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Accept': '*/*',
        'Referer': f'https://chaturbate.com/{room_slug}/',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://chaturbate.com',
        'Content-Type': f'multipart/form-data; boundary=----{boundary}',
        'Cookie': 'csrftoken=ZF2KoQPEfT3ikgEEvhx4Ht4Dfg9LOo3f; stcki="Eg6Gdq=1"; agreeterms=1;'
    }
    
    # Build multipart form data exactly as in the curl request
    payload = (
        f'------{boundary}\r\n'
        f'Content-Disposition: form-data; name="room_slug"\r\n\r\n'
        f'{room_slug}\r\n'
        f'------{boundary}\r\n'
        f'Content-Disposition: form-data; name="bandwidth"\r\n\r\n'
        f'high\r\n'
        f'------{boundary}\r\n'
        f'Content-Disposition: form-data; name="current_edge"\r\n\r\n'
        f'edge20-mad.live.mmcdn.com\r\n'
        f'------{boundary}\r\n'
        f'Content-Disposition: form-data; name="exclude_edge"\r\n\r\n'
        f'\r\n'
        f'------{boundary}\r\n'
        f'Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n\r\n'
        f'ZF2KoQPEfT3ikgEEvhx4Ht4Dfg9LOo3f\r\n'
        f'------{boundary}--\r\n'
    )
    
    try:
        proxy_dict = get_random_proxy()
        response = requests.post(
            url,
            headers=headers,
            data=payload.encode('utf-8'),
            proxies=proxy_dict,
            timeout=10,
            verify=False
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('room_status') == 'offline':
            return {'error': 'room_offline', 'message': 'Stream is offline'}
        
        hls_url = result.get("hls_url") or result.get("url")
        if hls_url:
            result["hls_url"] = hls_url
            return result
        
        return None
    except Exception as e:
        logging.error(f"Curl-method request failed: {str(e)}")
        return None

def scrape_chaturbate_data(url, progress_callback=None):
    """Enhanced Chaturbate scraper that searches for any .m3u8 URL in XHR network requests with realtime progress updates"""
    try:
        # Initial URL validation
        if not url or 'chaturbate.com/' not in url:
            raise ValueError("Invalid Chaturbate URL")

        # Progress tracking helper function
        def update_progress(p, m):
            if progress_callback:
                progress_callback(p, m)

        update_progress(10, "Extracting room slug")
        room_slug = extract_room_slug(url)

        # First, try fetching the HLS URL via the API endpoint
        update_progress(30, "Fetching HLS URL via API")
        result = get_hls_url(room_slug)
        
        # If the primary API method fails, try the curl-based method as fallback
        if not result or 'error' in result or not result.get('hls_url'):
            update_progress(35, "Primary method failed, trying curl-based fallback")
            result = fetch_chaturbate_hls_with_curl_method(room_slug)
        
        if not result:
            raise ValueError("Empty response from Chaturbate API")
        if 'error' in result:
            error_msg = result.get('message', 'Unknown error')
            raise RuntimeError(f"Chaturbate API error: {error_msg}")

        hls_url = result.get("hls_url") or result.get("url")
        # If both API methods fail, force fallback to network search
        if not hls_url or ".m3u8" not in hls_url:
            update_progress(40, "API methods failed, falling back to browser scraping")
            hls_url = None
        else:
            # If we have a valid HLS URL from either API method, return early
            update_progress(100, "Scraping complete")
            return {
                "status": "online",
                "streamer_username": room_slug,
                "chaturbate_m3u8_url": hls_url,
            }

        # Use Selenium Wire with proxy to capture any .m3u8 URL from XHR network requests
        update_progress(50, "Searching XHR requests for .m3u8 URL")
        
        # Use our enhanced driver creation function with proxy support
        driver = create_selenium_driver_with_proxy(headless=True)
        
        try:
            driver.scopes = [r'.*\.m3u8.*']
            driver.get(url)
            found_url = None
            timeout = 15  # seconds timeout for waiting network traffic
            start_time = time.time()

            while time.time() - start_time < timeout:
                elapsed = time.time() - start_time
                # Update progress dynamically: ranges from 50% to 80%
                progress_percent = 50 + int((elapsed / timeout) * 30)
                update_progress(progress_percent, f"Waiting for stream URL... {int(elapsed)}s elapsed")
                for request in driver.requests:
                    if request.response and ".m3u8" in request.url:
                        found_url = request.url.split('?')[0]  # Remove query parameters if present
                        break
                if found_url:
                    break
                time.sleep(1)

            if found_url:
                hls_url = found_url
            else:
                raise RuntimeError("M3U8 URL not found in network requests")
        finally:
            driver.quit()

        # Validate that the found URL is in a proper format
        if not re.match(r"https?://[^\s]+\.m3u8", hls_url):
            raise ValueError("Invalid HLS URL format detected")

        update_progress(100, "Scraping complete")
        return {
            "status": "online",
            "streamer_username": room_slug,
            "chaturbate_m3u8_url": hls_url,
        }

    except Exception as e:
        error_msg = f"Scraping failed: {str(e)}"
        logging.error(error_msg)
        if progress_callback:
            progress_callback(100, error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "details": str(e)
        }

# --- Existing Functions Remain Unchanged ---
def fetch_page_content(url, use_selenium=False):
    """
    Fetch the HTML content of the provided URL.
    Uses a robust set of headers to mimic a real browser.
    
    Args:
        url (str): The URL of the webpage to scrape.
        use_selenium (bool): If True, uses Selenium to fetch the page.
        
    Returns:
        str: The HTML content of the webpage.
        
    Raises:
        Exception: If the request fails.
    """
    if use_selenium:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--ignore-certificate-errors")
        unique_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={unique_user_data_dir}")
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            time.sleep(5)
            return driver.page_source
        finally:
            driver.quit()
    else:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) "
                "Gecko/20100101 Firefox/112.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://chaturbate.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        session = requests.Session()
        try:
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error("Direct request failed: %s. Trying Selenium...", e)
            return fetch_page_content(url, use_selenium=True)


def extract_m3u8_urls(html_content):
    """
    Extract m3u8 URLs from the given HTML content using a regular expression.
    
    Args:
        html_content (str): The HTML content to search within.
    
    Returns:
        list: A list of found m3u8 URLs.
    """
    pattern = r'https?://[^\s"\']+\.m3u8'
    urls = re.findall(pattern, html_content)
    return urls


def fetch_m3u8_from_page(url, timeout=90):
    """Fetch the M3U8 URL from the given page using Selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")
    unique_user_data_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={unique_user_data_dir}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.scopes = ['.*\\.m3u8']

    try:
        logging.info(f"Opening URL: {url}")
        driver.get(url)
        time.sleep(5)
        found_url = None
        elapsed = 0
        while elapsed < timeout:
            for request in driver.requests:
                if request.response and ".m3u8" in request.url:
                    found_url = request.url
                    logging.info(f"Found M3U8 URL: {found_url}")
                    break
            if found_url:
                break
            time.sleep(1)
            elapsed += 1
        return found_url if found_url else None
    except Exception as e:
        logging.error(f"Error fetching M3U8 URL: {e}")
        return None
    finally:
        driver.quit()


def scrape_stripchat_data(url, progress_callback=None):
    """
    Enhanced Stripchat scraper combining network interception with direct JavaScript
    player state inspection to reliably capture HLS URLs.
    """

    def update_progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    try:
        update_progress(15, "Initializing browser")

        # Configure Chrome options with enhanced stealth settings
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/119.0.0.0 Safari/537.36")

        # Advanced anti-detection configuration
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Initialize WebDriver with enhanced options
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd("Network.enable", {})

        try:
            update_progress(20, "Loading page")
            driver.get(url)
            
            # Attempt to extract HLS URL directly from player state
            update_progress(30, "Inspecting player state")
            hls_url = None
            js_script = """
            var player = Array.from(document.querySelectorAll('video'))
                .find(v => v.__vue__ && v.__vue__.$player);
            if (player) {
                return player.__vue__.$player._lastKnownStreamConfig?.hlsStreamUrl || 
                    (player.__vue__.$player._playerInstance?.hls?.url);
            }
            return null;
            """
            
            try:
                hls_url = driver.execute_script(js_script)
                if hls_url and "m3u8" in hls_url:
                    logging.debug(f"Direct HLS URL from player state: {hls_url}")
            except Exception as js_error:
                logging.warning(f"JS player inspection failed: {js_error}")

            # If direct method failed, fall back to network interception
            if not hls_url:
                update_progress(43, "Monitoring network requests")
                m3u8_urls = set()
                start_time = time.time()
                max_wait = 60
                
                while time.time() - start_time < max_wait:
                    for request in driver.requests:
                        if (request.response and 
                            request.method == "GET" and 
                            "m3u8" in request.url and 
                            "segment" not in request.url):
                            clean_url = request.url.split('?')[0]
                            m3u8_urls.add(clean_url)
                    if m3u8_urls:
                        break
                    time.sleep(1)

                # Prioritize URLs containing 'chunklist' or 'index'
                hls_url = next((url for url in m3u8_urls 
                              if any(kw in url for kw in ['chunklist', 'index'])), None)
                if not hls_url and m3u8_urls:
                    hls_url = next(iter(m3u8_urls))

            # Validation and error handling
            if not hls_url:
                raise RuntimeError("HLS URL not found through any method")

            update_progress(69, "Validating stream configuration")
            if not re.match(r"https?://[^\s]+\.m3u8", hls_url):
                raise ValueError("Invalid HLS URL format")

            # Extract additional metadata from player state
            metadata_script = """
            return {
                resolutions: window.__NUXT__?.data?.player?.data?.resolutions,
                isLive: window.__NUXT__?.data?.player?.data?.isLive,
                broadcaster: window.__NUXT__?.data?.player?.data?.username
            }
            """
            metadata = driver.execute_script(metadata_script) or {}
            
            update_progress(100, "Stream data captured successfully")
            return {
                "status": "online",
                "streamer_username": metadata.get("broadcaster") or url.split("/")[-1],
                "stripchat_m3u8_url": hls_url,  # Changed from hls_url to stripchat_m3u8_url
                "resolutions": metadata.get("resolutions", []),
                "is_live": metadata.get("isLive", True),
                "detection_method": "player_state" if hls_url else "network_interception"
            }

        except Exception as e:
            logging.error(f"Scraping error: {str(e)}")
            raise

        finally:
            driver.quit()

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": "scraping_error",
            "platform": "stripchat"
        }
def run_scrape_job(job_id, url):
    """Run a scraping job and update progress interactively."""
    update_job_progress(job_id, 0, "Starting scrape job")
    if "chaturbate.com" in url:
        result = scrape_chaturbate_data(url, progress_callback=lambda p, m: update_job_progress(job_id, p, m))
    elif "stripchat.com" in url:
        result = scrape_stripchat_data(url, progress_callback=lambda p, m: update_job_progress(job_id, p, m))
    else:
        logging.error("Unsupported platform for URL: %s", url)
        result = None
    if result:
        scrape_jobs[job_id]["result"] = result
    else:
        scrape_jobs[job_id]["error"] = "Scraping failed"
    update_job_progress(job_id, 100, scrape_jobs[job_id].get("error", "Scraping complete"))

def run_stream_creation_job(app, job_id, room_url, platform, agent_id):
    """
    Handles the creation of a streaming connection with fun, quirky progress updates.
    
    This function connects to streaming platforms (Chaturbate or Stripchat), extracts
    stream information, saves it to a database, assigns it to an agent if requested,
    and sends notifications when complete.
    
    Features entertaining progress messages that make technical processes more fun!
    """
    with app.app_context():
        start_time = time.time()
        # Initialize job with fun starting message
        stream_creation_jobs[job_id] = {
            'start_time': start_time,
            'progress': 0,
            'message': 'Initializing quantum flux capacitors',
            'estimated_time': 120,
            'last_updated': start_time,
            'error': None,
            'stream': None
        }
        
        # Define progress phases with quirky technical messages for each step
        progress_markers = {
            'validation': {'start': 0, 'end': 10, 'microsteps': 5},
            'scraping': {'start': 10, 'end': 55, 'microsteps': 12},
            'database': {'start': 55, 'end': 75, 'microsteps': 8},
            'assignment': {'start': 75, 'end': 90, 'microsteps': 6},
            'finalization': {'start': 90, 'end': 100, 'microsteps': 5}
        }
        
        # Fun, quirky messages for each phase to entertain users while they wait
        phase_messages = {
            'validation': [
                "Initializing neural pathways",
                "Verifying dimensional integrity",
                "Checking stream paradox coefficients",
                "Validating URL quantum state",
                "Confirming reality alignment"
            ],
            'scraping': [
                f"Deploying reconnaissance nanobots to {platform}",
                "Executing stealth protocol alpha",
                "Decrypting stream topology",
                "Establishing subspace connection",
                "Bypassing anti-scraping shields",
                "Extracting stream data packets",
                "Compressing hyperdata",
                "Decoding stream metadata",
                "Analyzing transmission integrity",
                "Computing bandwidth prerequisites",
                "Validating data fidelity",
                "Finalizing stream parameters"
            ],
            'database': [
                "Warming up the database hyperdrive",
                "Constructing data architecture",
                "Initializing transaction wormhole",
                "Aligning quantum database indices",
                "Optimizing data insertion vectors",
                "Establishing persistence field",
                "Committing to spacetime continuum",
                "Synchronizing parallel universes"
            ],
            'assignment': [
                "Locating agent in the multiverse",
                "Verifying agent clearance level",
                "Establishing secure neural link",
                "Creating agent-stream quantum entanglement",
                "Configuring assignment algorithms",
                "Recording assignment in universal ledger"
            ],
            'finalization': [
                "Engaging notification hyperdrive",
                "Broadcasting across all dimensions",
                "Notifying the Telegram Council",
                "Integrating with cosmic mesh network",
                "Completing stream initialization"
            ]
        }
        
        # Progress tracking variables
        last_progress = 0
        last_micro_update = time.time() - 2
        micro_interval = 0.7  # seconds between micro-updates
        
        # Helper function to update progress with fun messages
        def update_with_phase(phase, subprogress=0, custom_message=None):
            nonlocal last_progress, last_micro_update
            
            if phase not in progress_markers:
                return
                
            markers = progress_markers[phase]
            # Calculate overall progress percentage
            phase_progress = markers['start'] + (markers['end'] - markers['start']) * (subprogress / 100)
            
            # Ensure progress never goes backward
            phase_progress = max(int(phase_progress), last_progress)
            
            # Select a quirky message based on progress
            current_time = time.time()
            if custom_message is None and current_time - last_micro_update >= micro_interval:
                micro_step = min(int(subprogress / (100 / len(phase_messages[phase]))), len(phase_messages[phase]) - 1)
                phase_message = phase_messages[phase][micro_step]
                last_micro_update = current_time
            else:
                phase_message = custom_message or f"Processing {phase}"
            
            # Update estimated time remaining
            elapsed = current_time - start_time
            progress_delta = phase_progress - last_progress
            if progress_delta > 0:
                # Dynamic time estimation that decreases as progress increases
                estimated_total = elapsed * (100 / max(phase_progress, 1)) * 0.9
                remaining = max(estimated_total - elapsed, 0)
                
                # Update the job progress
                update_stream_job_progress(
                    job_id, 
                    phase_progress, 
                    phase_message,
                    estimated_time=int(remaining)
                )
                
                last_progress = phase_progress
        
        # Updates the job progress record
        def update_stream_job_progress(job_id, progress, message, estimated_time=None):
            if job_id in stream_creation_jobs:
                stream_creation_jobs[job_id].update({
                    'progress': int(progress),  # Always use whole numbers
                    'message': message,
                    'last_updated': time.time()
                })
                if estimated_time is not None:
                    stream_creation_jobs[job_id]['estimated_time'] = estimated_time
        
        try:
            # PHASE 1: VALIDATION - Check if we can proceed
            for i in range(progress_markers['validation']['microsteps']):
                progress_pct = (i / progress_markers['validation']['microsteps']) * 100
                update_with_phase('validation', progress_pct)
                time.sleep(0.2)  # Small delay for visual feedback
            
            # PHASE 2: SCRAPING - Get stream data from the platform
            update_with_phase('scraping', 5, f"Deploying data extraction probes to {platform}")
            
            try:
                # Progress callback for scraping phase
                def scraping_progress_callback(percent, message):
                    # Add some randomness to make it seem more "alive"
                    jitter = random.uniform(-2, 2)
                    adj_percent = max(0, min(100, percent + jitter))
                    update_with_phase('scraping', adj_percent)
                
                # Try scraping with retries if needed
                max_retries = 3
                retry_count = 0
                scraped_data = None
                
                while retry_count < max_retries:
                    try:
                        if platform == "chaturbate":
                            scraped_data = scrape_chaturbate_data(
                                room_url, 
                                progress_callback=scraping_progress_callback
                            )
                        else:
                            scraped_data = scrape_stripchat_data(
                                room_url,
                                progress_callback=scraping_progress_callback
                            )
                            # Fix: Handle different key naming for Stripchat
                            if scraped_data and 'status' in scraped_data and scraped_data['status'] == 'online':
                                if 'hls_url' in scraped_data:
                                    # Copy the hls_url to stripchat_m3u8_url key
                                    scraped_data['stripchat_m3u8_url'] = scraped_data['hls_url']
                        
                        # If we got here, scraping succeeded
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise
                        
                        retry_delay = 2 * retry_count  # Exponential backoff
                        update_with_phase('scraping', 
                                         40 + retry_count * 10, 
                                         f"Recalibrating scraper algorithms (attempt {retry_count+1}/{max_retries})")
                        time.sleep(retry_delay)

                # Verify scraping results
                update_with_phase('scraping', 85, "Verifying data integrity")
                
                if not scraped_data or 'status' not in scraped_data:
                    raise RuntimeError("Invalid scraping response - the matrix has glitched")
                
                update_with_phase('scraping', 90, "Analyzing stream quantum state")
                if scraped_data['status'] != 'online':
                    raise RuntimeError(scraped_data.get('message', 'Stream is offline or hiding in another dimension'))
                    
                update_with_phase('scraping', 95, "Confirming hyperlink stability")
                expected_key = f"{platform}_m3u8_url"
                if not scraped_data.get(expected_key):
                    raise RuntimeError(f"Missing stream URL (the {expected_key} has vanished)")
                
                update_with_phase('scraping', 100, "Stream data successfully extracted from the ether")

            except Exception as e:
                update_with_phase('scraping', 100, f"Scraping sensors malfunctioned: {str(e)}")
                raise RuntimeError(f"Scraping failed: {str(e)}") from e

            # PHASE 3: DATABASE - Save the stream data
            update_with_phase('database', 10, "Preparing database quantum entanglement")
            try:
                for i in range(progress_markers['database']['microsteps']):
                    progress_pct = (i / progress_markers['database']['microsteps']) * 100
                    update_with_phase('database', progress_pct)
                    time.sleep(0.1)
                
                # FIX: Use a single transaction for checking existence and creating the stream
                with db.session.begin():
                    # First check if the stream exists within the transaction
                    existing_stream = db.session.query(Stream).filter_by(room_url=room_url).with_for_update().first()
                    if existing_stream:
                        raise ValueError(f"Stream already exists with URL: {room_url}")
                    
                    # Create the appropriate stream object based on platform
                    if platform == "chaturbate":
                        stream = ChaturbateStream(
                            room_url=room_url,
                            streamer_username=scraped_data['streamer_username'],
                            chaturbate_m3u8_url=scraped_data['chaturbate_m3u8_url'],
                            type='chaturbate'
                        )
                    else:
                        stream = StripchatStream(
                            room_url=room_url,
                            streamer_username=scraped_data['streamer_username'],
                            stripchat_m3u8_url=scraped_data['stripchat_m3u8_url'],
                            type='stripchat'
                        )
                    
                    # Add and flush but don't commit yet
                    db.session.add(stream)
                    db.session.flush()
                
                # Refresh to get ID and other generated values
                db.session.refresh(stream)
                update_with_phase('database', 100, "Stream record materialized in the database dimension")
                
            except Exception as e:
                # Handle specific database constraint violation
                if "violates unique constraint" in str(e) and "room_url" in str(e):
                    raise RuntimeError(f"Stream already exists with this URL. Please try a different URL.")
                else:
                    raise RuntimeError(f"Database quantum flux error: {str(e)}")

            # PHASE 4: AGENT ASSIGNMENT - Connect stream to an agent if requested
            stream_creation_jobs[job_id]["progress"] = 95
            stream_creation_jobs[job_id]["message"] = "Finalizing stream creation..."
            
            if agent_id:
                update_with_phase('assignment', 20, "Establishing agent neural connection")
                try:
                    with app.app_context():
                        try:
                            from models import Assignment
                            assignment = Assignment(agent_id=agent_id, stream_id=stream.id)
                            db.session.add(assignment)
                            db.session.commit()
                            update_with_phase('assignment', 100, "Stream created and assigned successfully.")
                        except Exception as e:
                            update_with_phase('assignment', 100, f"Stream created but assignment failed: {str(e)}")
                            # Log the error but don't fail the stream creation
                            logging.error(f"Assignment creation failed: {str(e)}")
                except Exception as e:
                    raise RuntimeError(f"Assignment failed: {str(e)}")
            else:
                # Skip assignment phase if no agent_id
                update_with_phase('assignment', 100, "No agent to assign - running in autonomous mode")
                
            # PHASE 5: FINALIZATION - Send notifications and wrap up
            update_with_phase('finalization', 30, "Charging notification particle accelerator")
            try:
                # Simulate notification work with micro-updates
                for i in range(progress_markers['finalization']['microsteps']):
                    progress_pct = (i / progress_markers['finalization']['microsteps']) * 100
                    update_with_phase('finalization', progress_pct)
                    time.sleep(0.15)
                
                # Send notifications 
                send_telegram_notifications(
                    platform,
                    stream.streamer_username,
                    room_url
                )
                update_with_phase('finalization', 95, "Notifications broadcasted across the multiverse")
            except Exception as e:
                logging.error("Notifications failed: %s", str(e))
                update_with_phase('finalization', 95, "Notification subspace transmission jammed (non-critical)")
            
            # Success! We're done!
            update_stream_job_progress(job_id, 100, "Stream successfully created and ready for observation")
            stream_creation_jobs[job_id].update({
                'stream': stream.serialize(),
                'stream_data': stream.serialize(),  # Added as per your request
                'estimated_time': 0
            })

        except Exception as e:
            # Handle any errors that occurred
            error_msg = f"Creation failed: {str(e)}"
            logging.error("Full error: %s", error_msg)
            if hasattr(e, '__cause__'):
                logging.error("Root cause: %s", str(e.__cause__))
                
            stream_creation_jobs[job_id].update({
                'error': error_msg,
                'progress': 100,
                'message': f"Mission aborted: {error_msg}"
            })

        finally:
            # Clean up resources
            try:
                db.session.close()
            except Exception as e:
                logging.warning("Session close anomaly detected: %s", str(e))
            
            # Log completion metrics
            completion_time = time.time() - start_time
            logging.info(f"Stream creation job {job_id} completed in {completion_time:.2f} seconds")

def send_telegram_notifications(platform, streamer, room_url):
    """Robust notification handler"""
    try:
        recipients = User.query.filter(User.telegram_chat_id.isnot(None)).all()
        if not recipients:
            return

        message = (
            f"New Stream: {streamer}\n"
            f"Platform: {platform}\n"
            f"URL: {room_url}"
        )
        
        for recipient in recipients:
            try:
                executor.submit(
                    send_text_message,
                    message=message,
                    chat_id=recipient.chat_id
                )
            except Exception as e:
                logging.error("Failed to notify %s: %s", 
                            recipient.chat_id, str(e))
                
    except Exception as e:
        logging.error("Notification system error: %s", str(e))
def fetch_chaturbate_chat_history(room_slug):
    """Fetch chat history from Chaturbate's API endpoint."""
    url = "https://chaturbate.com/push_service/room_history/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://chaturbate.com/{room_slug}/",
        "Origin": "https://chaturbate.com",
        "Cookie": 'csrftoken=vfO2sk8hUsSXVILMJwtcyGqhPy6WqwhH; stcki="Eg6Gdq=1,kHDa2i=1"'
    }
    
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json().get("0", {}).values()
    except Exception as e:
        logging.error(f"Chat history fetch error: {str(e)}")
        return []


def refresh_chaturbate_stream(room_slug):
    """
    Refresh the m3u8 URL for a Chaturbate stream using the proxy-enabled scraping function.
    
    Args:
        room_slug (str): The room slug (streamer username).
    
    Returns:
        str or None: The new m3u8 URL if successful, or None if an error occurred.
    """
    try:
        # Construct the Chaturbate room URL
        room_url = f"https://chaturbate.com/{room_slug}/"
        
        # Use our enhanced scraper that consistently uses proxies
        scraped_data = scrape_chaturbate_data(room_url)
        
        # Validate the response
        if not scraped_data or scraped_data.get('status') != 'online':
            logging.error("Scraping failed or stream offline for %s", room_slug)
            return None
        
        new_url = scraped_data.get('chaturbate_m3u8_url')
        if not new_url:
            logging.error("No valid m3u8 URL found for room slug: %s", room_slug)
            return None
        
        # Update the database
        stream = ChaturbateStream.query.filter_by(streamer_username=room_slug).first()
        if stream:
            stream.chaturbate_m3u8_url = new_url
            db.session.commit()
            logging.info("Updated stream '%s' with new m3u8 URL: %s", room_slug, new_url)
            return new_url
        else:
            logging.info("No existing stream found, but valid URL found: %s", new_url)
            return new_url
    
    except Exception as e:
            logging.error("Error refreshing stream for room slug %s: %s", room_slug, str(e))
            db.session.rollback()
            return None


def refresh_stripchat_stream(room_url: str) -> str:
    """
    Refresh the M3U8 URL for a Stripchat stream using the proxy-enabled scraping function.
    
    Args:
        room_url (str): The full URL of the Stripchat room.
    
    Returns:
        str: The new M3U8 URL if successful, None otherwise.
    """
    try:
        # Use our enhanced scraper with proxy support
        scraped_data = scrape_stripchat_data(room_url)
        
        # Validate the response
        if not scraped_data or scraped_data.get('status') != 'online':
            logging.error("Scraping failed or stream offline for %s", room_url)
            return None
        
        new_url = scraped_data.get("stripchat_m3u8_url")
        if not new_url:
            logging.error("No valid m3u8 URL found for URL: %s", room_url)
            return None
        
        # Update the database
        stream = StripchatStream.query.filter_by(room_url=room_url).first()
        if stream:
            stream.stripchat_m3u8_url = new_url
            db.session.commit()
            return new_url
        return None
    except Exception as e:
        logging.error(f"Error refreshing Stripchat stream: {str(e)}")
        db.session.rollback()
        return None

def validate_proxy(proxy, timeout=3):
    """
    Check if a proxy is working by making a test request
    
    Args:
        proxy (str): Proxy in format IP:PORT
        timeout (int): Request timeout in seconds
        
    Returns:
        bool: True if proxy is working, False otherwise
    """
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    
    try:
        response = requests.get(
            "https://httpbin.org/ip", 
            proxies=proxies, 
            timeout=timeout,
            verify=False
        )
        return response.status_code == 200
    except:
        return False

def get_validated_proxies(proxy_list, max_count=20):
    """
    Filter and return only working proxies
    
    Args:
        proxy_list (list): List of proxies to validate
        max_count (int): Maximum number of validated proxies to return
        
    Returns:
        list: List of validated proxies
    """
    validated = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(validate_proxy, proxy): proxy for proxy in proxy_list}
        
        for future in as_completed(futures):
            proxy = futures[future]
            try:
                if future.result():
                    validated.append(proxy)
                    if len(validated) >= max_count:
                        break
            except Exception:
                pass
    
    return validated

def proxy_updater_thread():
    """Background thread to update proxy list periodically"""
    global PROXY_LIST, PROXY_LIST_LAST_UPDATED
    
    while True:
        try:
            # Try different methods to get fresh proxies
            new_proxies = update_proxy_list() or get_proxies_with_library() or scrape_free_proxy_list()
            
            if new_proxies and len(new_proxies) >= 10:
                with PROXY_LOCK:
                    PROXY_LIST = new_proxies
                    PROXY_LIST_LAST_UPDATED = time.time()
                    logging.info(f"[Background] Updated proxy list with {len(PROXY_LIST)} proxies at {datetime.now()}")
        except Exception as e:
            logging.error(f"Error in proxy updater thread: {str(e)}")
        
        # Sleep for the update interval
        time.sleep(PROXY_UPDATE_INTERVAL)

# Start the background thread when the module is imported
proxy_thread = threading.Thread(target=proxy_updater_thread, daemon=True)
proxy_thread.start()


