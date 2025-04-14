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

# Disable insecure request warnings due to disabled SSL certificate verification.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import models and database session for stream creation.
from models import Stream, ChaturbateStream, StripchatStream, Assignment, TelegramRecipient, User
from extensions import db
from notifications import send_text_message

# Global dictionaries to hold job statuses.
scrape_jobs = {}
stream_creation_jobs = {}
executor = ThreadPoolExecutor(max_workers=5)  # Thread pool for parallel scraping

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


# --- Updated Proxy List from free-proxy-list.net (Updated at 2025-03-28 21:42:02 UTC) ---
PROXY_LIST = [

"52.67.10.183:80",
"200.250.131.218:80",
"152.230.215.123:80",
"85.214.107.177:80",
"154.0.14.116:3128",
"141.95.238.126:8080",
"91.134.55.236:8080",
"219.65.73.81:80",
"170.106.135.2:13001",
"43.153.36.22:3334",
"188.68.52.244:80",
"43.153.117.40:13001",
"49.51.250.227:13001",
"43.153.117.193:13001",
"43.153.105.141:13001",
"43.130.32.94:13001",
"170.106.137.158:13001",
"170.106.143.168:13001",
"79.127.158.225:8081",
"49.51.179.85:13001",
"170.106.100.130:13001",
"43.135.161.247:13001",
"170.106.67.179:13001",
"43.153.78.185:13001",
"49.51.197.116:13001",
"170.106.64.187:13001",
"43.135.183.46:13001",
"43.135.129.111:13001",
"43.153.16.149:13001",
"43.153.4.125:13001",
"170.106.196.118:13001",
"170.106.80.237:13001",
"43.159.129.136:13001",
"170.106.82.224:13001",
"49.51.203.51:13001",
"43.135.138.21:13001",
"43.135.172.243:13001",
"51.91.237.124:8080",
"170.106.173.254:13001",
"43.135.179.180:13001",
"43.130.16.92:13001",
"43.130.38.18:13001",
"43.130.0.130:13001",
"170.106.198.54:13001",
"43.130.57.165:13001",
"170.106.192.157:13001",
"170.106.194.126:13001",
"43.135.134.89:13001",
"43.135.130.88:13001",
"43.130.2.30:13001",
"170.106.169.110:13001",
"43.135.164.4:13001",
"43.153.28.45:13001",
"43.130.48.100:13001",
"43.130.37.196:13001",
"43.130.29.139:13001",
"43.135.164.2:13001",
"43.130.42.164:13001",
"43.153.79.9:13001",
"65.49.14.6:3128",
"47.88.137.92:5020",
"43.153.92.57:13001",
"43.153.100.212:13001",
"43.153.79.15:13001",
"43.153.2.3:13001",
"103.213.218.22:13137",
"37.114.192.104:3128",
"51.44.176.151:20202",
"18.223.25.15:80",
"212.33.205.55:3128",
"188.166.230.109:31028",
"65.49.2.99:3128",
"49.51.249.217:13001",
"54.37.214.253:8080",
"63.32.1.88:3128",
"121.200.50.33:3128",
"43.153.21.33:13001",
"43.153.35.252:13001",
"8.219.97.248:80",
"8.210.17.35:9443",
"62.210.15.199:80",
"117.103.68.38:9941",
"15.236.106.236:3128",
"47.252.29.28:11222",
"23.247.136.248:80",
"3.126.147.182:80",
"35.72.118.126:80",
"43.202.154.212:80",
"3.127.62.252:80",
"18.228.149.161:80",
"3.127.121.101:80",
"3.78.92.159:3128",
"51.16.199.206:3128",
"52.63.129.110:3128",
"52.65.193.254:3128",
"51.16.179.113:1080",
"3.212.148.199:3128",
"54.248.238.110:80",
"44.219.175.186:80",
"162.223.90.130:80"

]


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
        if not result:
            raise ValueError("Empty response from Chaturbate API")
        if 'error' in result:
            error_msg = result.get('message', 'Unknown error')
            raise RuntimeError(f"Chaturbate API error: {error_msg}")

        hls_url = result.get("hls_url") or result.get("url")
        # If the API URL is missing or invalid, force fallback to network search
        if not hls_url or ".m3u8" not in hls_url:
            hls_url = None

        # Use Selenium Wire to capture any .m3u8 URL from XHR network requests
        update_progress(50, "Searching XHR requests for .m3u8 URL")
        from seleniumwire import webdriver
        from selenium.webdriver.chrome.options import Options

        # Configure headless Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--ignore-certificate-errors")
        # Initialize Selenium Wire webdriver and filter for .m3u8 requests
        driver = webdriver.Chrome(options=chrome_options)
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
    Enhanced Stripchat scraper that sends a watch-model API POST request before scraping
    and intercepts network XHR requests to capture HLS (m3u8) URL.

    Args:
        url (str): The Stripchat stream URL.
        progress_callback (callable, optional): Callback function for progress updates.

    Returns:
        dict: Stream status and extracted m3u8 URL or error details.
    """

    def update_progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    try:
        update_progress(5, "Initializing scraping")
        
        # Extract model ID and name from URL
        streamer_username = url.rstrip("/").split("/")[-1]
        
        # Send logs API POST request before starting scraping (existing code)
        update_progress(10, "Sending logs API request")
        logs_api_url = "https://stripchat.com/api/front/v2/logs"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": url,
            "content-type": "application/json",
            "front-version": "11.1.49",
            "Origin": "https://stripchat.com",
            "Connection": "keep-alive",
            "Cookie": "_cfuvid=1EsBEUyo0jR.KGb5vqXWzIewBAYG6t7nLi1P8T.cCuw-1744418142627-0.0.1.1-604800000; ABTest_ab_private_animations_key=A_623; cf_clearance=udvCJbTg1DRIr7SY3SepjSXKRlRzcRT_vzn93tXRIrM-1744418159-1.2.1.1-75I7qEtAeXnNuxh8kyLmBW5I6TnghGwuKqBr_qmz1B2rZdJCwV8zQWfJDzIvujQpC0Wn6rAEaan0clyp3kps2BWUTdfPrZ6WtzaT.aVUZTN0yHzajq6TaNlC2mtgukLJggH7irqjvHTi7uES.luqOs4yPbYM1alyf79M3.m6c4N1TC4JMvY83VKqehJ9TrHnOMxh.sWHqd63sdqaq7H1txwTEIpxw0hj3rJv3KagOmBcYbPmw4iuluilxJ1epw9_KEhxcrveJOrR1YwWASnMVffQ2FOTm.VJFxUAKcYh4z3J3CLzSG6VC1RkfBdOYrDkuPzfmBFS9Y3F6IOcKNJxRIot9Y0Oshei5RqNcjTevc0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=4",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "TE": "trailers"
        }
        
        logs_data = {
            "search": "userDevice",
            "data": {
                "league": None,
                "role": "studio",
                "deviceInfo": {
                    "os": "Linux",
                    "type": "desktop"
                },
                "deviceAdditional": {
                    "browser": {
                        "name": "Firefox",
                        "version": "135.0"
                    },
                    "os": {
                        "name": "Linux"
                    },
                    "platform": {
                        "type": "desktop"
                    },
                    "engine": {
                        "name": "Gecko",
                        "version": "20100101"
                    }
                }
            },
            "indexedData": {
                "tabId": "a369b6d8d6c8d262cd10085070209b48639233c5646b988090087557ed1c",
                "userRole": "studio",
                "userId": 194007038
            },
            "logLevel": "debug",
            "frontlog": 1,
            "csrfToken": "41a21dd3b454543d5b4cccacf5286813",
            "csrfTimestamp": "2025-04-12T00:36:00Z",
            "csrfNotifyTimestamp": "2025-04-13T12:36:00Z",
            "uniq": "9rmy3odvqkjuewiz"
        }
        
        try:
            # Send logs API request
            logs_response = requests.post(logs_api_url, json=logs_data, headers=headers, timeout=10)
            logs_response.raise_for_status()
            logging.info("Logs API request sent successfully")
        except Exception as e:
            logging.error(f"Logs API request failed: {str(e)}")
            # Continue with scraping even if logs API request fails
        
        # NEW: Send watch-model POST request based on provided curl command
        update_progress(15, "Sending watch-model request")
        try:
            watch_model_url = 'https://stripchat.com/api/front/users/194007038/watch-model'
            watch_model_headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'application/json',
                'Referer': url,
                'front-version': '11.1.49',
                'Origin': 'https://stripchat.com',
                'Connection': 'keep-alive',
                'Cookie': 'ABTest_ab_buy_tokens_refill_all_30_v2_key=N_623; ABTest_ab_dark_buy_tokens_big_part_key=B_623; ABTest_ab_dark_buy_tokens_small_part_key=N_623; ABTest_ab_improve_error_states_cards_payment_methods_key=A_623; ABTest_ab_send_tip_dialog_redesign_key=A_623; ABTest_ab_disable_ll_v2_key=X_623; isRecommendationDisabled=false; alreadyVisited=1; isVisitorsAgreementAccepted=1; guestWatchHistoryStartDate=2025-03-03T21%3A37%3A26.937Z; guestFavoriteIds=; c=%7B%22essential%22%3A%5B%22all%22%5D%2C%22thirdParties%22%3A%5B%22all%22%5D%7D; baseAmpl=%7B%22platform%22%3A%22Web%22%2C%22device_id%22%3A%228ztAvsvRoyTztzNUMJf90-%22%2C%22session_id%22%3A1744554624676%2C%22up%22%3A%7B%7D%7D; _ga_Q87RE2YE8G=GS1.1.1744554318.100.1.1744554623.0.0.0; _ga=GA1.1.756921033.1741037851; sCashGuestId=904aa620cf064549723b26e9bcd1ef984bce30707747a8a740c6868047002d0b; _vid_t=9+SLKb6RkOFsYjk6FW42QSGmL+/jyFtujOcjKDlbr+LJufeBW9twdOOmh120p2GW+WIPy89EUCdiUw==; stripchat_com_sessionRemember=1; USER_DATA=%7B%22attributes%22%3A%5B%7B%22key%22%3A%22USER_ATTRIBUTE_UNIQUE_ID%22%2C%22value%22%3A194007038%2C%22updated_at%22%3A1741647623655%7D%5D%2C%22subscribedToOldSdk%22%3Afalse%2C%22deviceUuid%22%3A%22e2847c3e-c199-4ba4-bcb0-a4839d90d10e%22%2C%22deviceAdded%22%3Atrue%7D; SESSION=%7B%22sessionKey%22%3A%225bee6270-c3a0-4df5-8d70-454b69e4cc75%22%2C%22sessionStartTime%22%3A%222025-04-13T14%3A25%3A26.514Z%22%2C%22sessionMaxTime%22%3A1800%2C%22customIdentifiersToTrack%22%3A%5B%5D%2C%22sessionExpiryTime%22%3A1744556432079%2C%22numberOfSessions%22%3A67%7D; datadome=8OnrZJDSPW_BuOWgNvICsZhrHjbSgXkjaFQoMqkWhYGIWeGs~Ygsc66N5XnXiuk8tFooi82GnwaLfAGnbmHMz4BhbfTAnreqndT0_I1wGvQZoC0dY9XNmt2M5pJx0BGJ; stripchat_com_sessionId=70c6b7d664ff77ef5720ec2e1033ae13312f554c25c56955d4f707151138; ABTest_dark_buy_tokens_all_users_10_v2_key=N_623; DEVICE_DATA=%7B%22deviceUniqueId%22%3A%226707d32d-25bc-4b5b-821b-8ef306dabfb5%22%7D; IDENTITY_MAP=%7B%22userIdentities%22%3A%7B%22uid%22%3A194007038%7D%2C%22previousIdentities%22%3A%7B%7D%2C%22previousIdentitiesUpdatedTime%22%3A0%7D; ABTest_ab_rec_new_name_key=N_623; cf_clearance=a8R6GEI.wpLriCG9e_OYBWtEWQZ5kMNmRr3bpBv8TAQ-1744554314-1.2.1.1-F3Afpg4fgbQQppyMy7XJkb6kRO2oZZCSllx339tHuLIVLr5Br4uilwVSTEZqc2Mu6zDzR3tqJ3L_jHIq3.lJLLr3cLx1gs4.32Y6TWJN2kY.D4X.SBP.SZyD9ItlHPsqSadvQvVwbfG4bMhVCeb5A2JVJ1CrvSoc7bNL9T04dmd74EeTRlZz.Z8H3tZjQnZXmzYf6QjX_uBLdxgM0F_6P5Myilpxp5hAok4SeGpcuYoSMcuKFlxnVw3kuk6PGWwKipf2cAoQ90.wGYRruX5NZsEuMXu44pCXEG5gFxSc.SOG6Xf.7xE6rolt7epyu5_5I0Hsvn4yUtH6r62qL8poX0SzCwn87H.QyYyUhuXkqW4; ABTest_ab_dark_buy_tokens_all_users_90_v2_key=B_623; ABTest_ab_private_animations_key=A_623; ABTest_ab_send_tip_dialog_redesign_paying_users_part_1_v2_key=N_623; ABTest_ab_update_pvt_activities_list_v2_key=C_623; AMP_19a23394ad=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI4enRBdnN2Um95VHp0ek5VTUpmOTAtJTIyJTJDJTIydXNlcklkJTIyJTNBJTIyMTk0MDA3MDM4JTIyJTJDJTIyc2Vzc2lvbklkJTIyJTNBMTc0NDU1NDYyNDY3NiUyQyUyMm9wdE91dCUyMiUzQWZhbHNlJTJDJTIybGFzdEV2ZW50VGltZSUyMiUzQTE3NDQ1NTQ2MjYzOTUlMkMlMjJsYXN0RXZlbnRJZCUyMiUzQTQ2OCUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMCU3RA==; _cfuvid=RJH4oht6LxL8BWyUlvpCVeQSdlfF.N0R0Z5qX2BaLVw-1744539834356-0.0.1.1-604800000; moe_uuid=e2847c3e-c199-4ba4-bcb0-a4839d90d10e; __cf_bm=Y1DNFQZjHz_7_WSBn9lxs0K2nt4GT0yfxzYZS1gzER4-1744554312-1.0.1.1-pAyHAmt2kcUdA5TUab5alARmYBL8gfCPNKqPL0BY0nnn1oylF62zPSOluLKAEKPsbDfdnKRthNgBTEnLmuEDnzQJM4z_QndoH9UgXheg12rw58ArW8wF8cohv8uU6rMV',
                'Priority': 'u=4',
                'Pragma': 'no-cache', 
                'Cache-Control': 'no-cache',
                'TE': 'trailers'
            }
            # Generate random timestamp for CSRF fields
            now = time.time()
            iso_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
            iso_notify = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 129600))  # +36 hours
            
            # Generate random string for 'uniq' field
            random_uniq = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(16))
            
            # Generate random model ID (for demonstration - in production this would be fetched)
            model_id = 178700660
            
            watch_model_data = {
                "model": {
                    "id": model_id,
                    "addedAt": iso_now
                },
                "csrfToken": "7320bf137b06c28d7c37d2477796543e",
                "csrfTimestamp": iso_now,
                "csrfNotifyTimestamp": iso_notify,
                "uniq": random_uniq
            }
            
            watch_response = requests.post(
                watch_model_url,
                headers=watch_model_headers,
                json=watch_model_data,
                timeout=10
            )
            watch_response.raise_for_status()
            logging.info("Watch-model request sent successfully")
        except Exception as e:
            logging.error(f"Watch-model request failed: {str(e)}")
            # Continue with scraping even if this request fails
        
        update_progress(20, "Initializing browser")

        # Configure modern Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/119.0.0.0 Safari/537.36")

        # Anti-detection settings
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Initialize Selenium Wire webdriver for network interception
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            update_progress(30, "Loading page")
            driver.get(url)
            
            # Wait up to 10 seconds for network traffic to capture m3u8 requests
            update_progress(50, "Waiting for network XHR requests")
            m3u8_urls = set()
            max_wait = 15  # Extended wait time
            start_time = time.time()
            while time.time() - start_time < max_wait:
                for request in driver.requests:
                    # Check only XHR requests that have a response and include m3u8 in URL
                    if request.response and request.method == "GET" and "m3u8" in request.url:
                        clean_url = request.url.split('?')[0]
                        m3u8_urls.add(clean_url)
                if m3u8_urls:
                    break
                time.sleep(1)
                # Update progress dynamically based on elapsed time
                elapsed = time.time() - start_time
                progress_percent = min(80, 50 + (elapsed/max_wait)*30)
                update_progress(progress_percent, "Waiting for stream URL")

            # Log candidate URLs for debugging purposes
            if m3u8_urls:
                logging.debug(f"Candidate m3u8 URLs: {list(m3u8_urls)}")
            else:
                logging.error("No m3u8 URLs found in intercepted XHR requests.")

            # Prioritize URLs containing 'chunklist' to ensure HLS segments
            m3u8_url = next((url for url in m3u8_urls if "chunklist" in url), None)
            # If none with 'chunklist', fall back to any candidate
            if not m3u8_url and m3u8_urls:
                m3u8_url = next(iter(m3u8_urls))

            if not m3u8_url:
                # Provide full network debug info if available
                network_debug = [req.url for req in driver.requests if "m3u8" in req.url]
                logging.error(f"No m3u8 URL found. Network debug info: {network_debug}")
                raise RuntimeError("M3U8 URL not found in network requests.")

            update_progress(85, "Validating stream URL")
            # Validate the m3u8 URL format
            if not re.match(r"https?://[^\s]+\.m3u8", m3u8_url):
                raise ValueError("Invalid M3U8 URL format detected.")

            update_progress(100, "Stream URL successfully captured")
            return {
                "status": "online",
                "streamer_username": streamer_username,
                "stripchat_m3u8_url": m3u8_url,
            }

        except Exception as e:
            # Save debug information in case of an error
            timestamp = int(time.time())
            
            

        finally:
            driver.quit()

    except Exception as e:
        error_msg = f"Stripchat scraping failed: {str(e)}"
        logging.error(error_msg)
        update_progress(100, error_msg)
        return {
            "status": "error",
            "message": error_msg,
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
    """Complete stream creation handler"""
    with app.app_context():
        # Initialize job record
        stream_creation_jobs[job_id] = {
            'start_time': time.time(),
            'progress': 0,
            'message': 'Initializing',
            'estimated_time': 120,
            'last_updated': time.time(),
            'error': None,
            'stream': None
        }
        
        try:
            # Phase 1: Validation
            update_stream_job_progress(job_id, 5, "Validating input")
            with db.session.begin():
                if db.session.query(Stream).filter_by(room_url=room_url).first():
                    raise ValueError(f"Stream exists: {room_url}")

            # Phase 2: Scraping
            update_stream_job_progress(job_id, 10, f"Scraping {platform}")
            scraped_data = None
            try:
                if platform == "chaturbate":
                    scraped_data = scrape_chaturbate_data(
                        room_url,
                        lambda p, m: update_stream_job_progress(
                            job_id, 10 + p*0.35, m)
                    )
                else:
                    scraped_data = scrape_stripchat_data(
                        room_url,
                        lambda p, m: update_stream_job_progress(
                            job_id, 10 + p*0.35, m)
                    )

                # Validate scraping results
                if not scraped_data or 'status' not in scraped_data:
                    raise RuntimeError("Invalid scraping response")
                
                if scraped_data['status'] != 'online':
                    raise RuntimeError(scraped_data.get('message', 'Scraping failed'))
                    
                if not scraped_data.get(f"{platform}_m3u8_url"):
                    raise RuntimeError("Missing stream URL")

            except Exception as e:
                raise RuntimeError(f"Scraping failed: {str(e)}") from e

            # Phase 3: Database
            update_stream_job_progress(job_id, 50, "Creating record")
            try:
                # In the section where the stream is created:
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
                    
                db.session.add(stream)
                db.session.commit()
                db.session.refresh(stream)
            except Exception as e:
                db.session.rollback()
                raise RuntimeError(f"Database error: {str(e)}")

            # Phase 4: Agent assignment
            if agent_id:
                update_stream_job_progress(job_id, 70, "Assigning agent")
                try:
                    if not User.query.get(agent_id):
                        raise ValueError("Invalid agent ID")
                        
                    assignment = Assignment(
                        agent_id=agent_id,
                        stream_id=stream.id
                    )
                    db.session.add(assignment)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    raise RuntimeError(f"Assignment failed: {str(e)}")

            # Phase 5: Finalization
            update_stream_job_progress(job_id, 90, "Finalizing")
            try:
                send_telegram_notifications(
                    platform,
                    stream.streamer_username,
                    room_url
                )
            except Exception as e:
                logging.error("Notifications failed: %s", str(e))

            # Success
            update_stream_job_progress(job_id, 100, "Stream created")
            stream_creation_jobs[job_id].update({
                'stream': stream.serialize(),
                'estimated_time': 0
            })

        except Exception as e:
            db.session.rollback()
            error_msg = f"Creation failed: {str(e)}"
            logging.error("Full error: %s", error_msg)
            if hasattr(e, '__cause__'):
                logging.error("Root cause: %s", str(e.__cause__))
                
            stream_creation_jobs[job_id].update({
                'error': error_msg,
                'progress': 100,
                'message': error_msg
            })

        finally:
            try:
                db.session.close()
            except Exception as e:
                logging.warning("Session close error: %s", str(e))


def send_telegram_notifications(platform, streamer, room_url):
    """Robust notification handler"""
    try:
        recipients = TelegramRecipient.query.all()
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
    Refresh the m3u8 URL for a Chaturbate stream using the scraping function.
    
    Args:
        room_slug (str): The room slug (streamer username).
    
    Returns:
        str or None: The new m3u8 URL if successful, or None if an error occurred.
    """
    try:
        # Construct the Chaturbate room URL
        room_url = f"https://chaturbate.com/{room_slug}/"
        
        # Scrape the updated data
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
    Refresh the M3U8 URL for a Stripchat stream using the scraping function.
    
    Args:
        room_url (str): The full URL of the Stripchat room.
    
    Returns:
        str: The new M3U8 URL if successful, None otherwise.
    """
    try:
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