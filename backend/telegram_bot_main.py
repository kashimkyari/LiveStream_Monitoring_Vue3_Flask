import os
import asyncio
import logging
import signal
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'https://monitor-backend.jetcamstudio.com:5000')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')

# Session persistence file
SESSION_FILE = "user_sessions.json"

# Conversation states
LOGIN, PASSWORD, ADD_STREAM_URL, ADD_STREAM_PLATFORM, ADD_STREAM_AGENT, TRIGGER_STREAM, KEYWORD, OBJECT = range(8)

# User session data
user_sessions = {}

def load_sessions():
    """Load user sessions from file."""
    global user_sessions
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r') as f:
                user_sessions = json.load(f)
                user_sessions = {int(k): v for k, v in user_sessions.items()}
                logger.info("Loaded user sessions from file")
    except Exception as e:
        logger.error(f"Error loading sessions: {str(e)}")

def save_sessions():
    """Save user sessions to file."""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(user_sessions, f)
        logger.info("Saved user sessions to file")
    except Exception as e:
        logger.error(f"Error saving sessions: {str(e)}")

# Load sessions at startup
load_sessions()

# Define keyboard layouts
def get_main_keyboard():
    """Create the main menu keyboard."""
    keyboard = [
        ["📺 Streams", "🔍 Detection Status"],
        ["🔔 Notifications", "🧰 Tools"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_streams_keyboard():
    """Create the streams submenu keyboard."""
    keyboard = [
        ["🟢 My Streams", "➕ Add Stream"],
        ["🔙 Back to Main Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_tools_keyboard():
    """Create the tools submenu keyboard."""
    keyboard = [
        ["📝 Keywords", "🎯 Objects"],
        ["🔙 Back to Main Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_platform_keyboard():
    """Create the platform selection keyboard."""
    keyboard = [
        ["Chaturbate", "Stripchat"],
        ["🔙 Cancel"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Create a simple back button keyboard."""
    keyboard = [["🔙 Back to Main Menu"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# API Helper Function
async def api_request(method, endpoint, data=None, session_id=None, params=None):
    """Make a request to the API."""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    cookies = {'session': session_id} if session_id else None
    
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=10)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, cookies=cookies, json=data, timeout=10)
        elif method.lower() == 'put':
            response = requests.put(url, headers=headers, cookies=cookies, json=data, timeout=10)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers, cookies=cookies, timeout=10)
        else:
            return {'error': 'Invalid HTTP method'}
        
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return response.json()
            except:
                return {'message': response.text}
        else:
            try:
                return {'error': f"API Error ({response.status_code}): {response.json().get('message', response.text)}"}
            except:
                return {'error': f"API Error ({response.status_code}): {response.text}"}
    
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return {'error': f"Connection error: {str(e)}"}

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    user = update.effective_user
    user_id = user.id
    chat_id = update.message.chat_id
    
    # Check if user is already logged in
    session = user_sessions.get(user_id, {'logged_in': False})
    
    if session.get('logged_in', False):
        # Verify session with API
        response = await api_request('get', 'agent/dashboard', session_id=session.get('session_id'))
        if 'error' not in response:
            await update.message.reply_text(
                f"👋 Welcome back, {user.first_name}! You're already logged in.\n\n"
                f"Your chat ID is: `{chat_id}`\n"
                "Use the menu to manage your streams and notifications.",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
    
    # Initialize session for new user
    user_sessions[user_id] = {'logged_in': False}
    save_sessions()
    
    welcome_message = (
        f"👋 Welcome, {user.first_name}! I'm your LiveStream Monitoring Bot.\n\n"
        f"Your chat ID is: `{chat_id}`\n"
        "Use this ID to set up notifications in the monitoring system.\n\n"
        "Please login to access all features:"
    )
    
    login_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Login", callback_data="login")]
    ])
    
    await update.message.reply_text(
        welcome_message, 
        reply_markup=login_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /help command."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    if not session.get('logged_in', False):
        await update.message.reply_text(
            "You need to login first. Use /start to begin.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login", callback_data="login")]
            ])
        )
        return
    
    help_text = (
        "🔹 *LiveStream Monitoring Bot Help* 🔹\n\n"
        "*Main Commands:*\n"
        "• /start - Start the bot and login\n"
        "• /help - Show this help message\n"
        "• /getid - Get your chat ID for notifications\n"
        "• /logout - Log out from the system\n\n"
        "*Main Features:*\n"
        "• 📺 *Streams* - View and manage your assigned streams\n"
        "• 🔍 *Detection Status* - Check monitoring status of streams\n"
        "• 🔔 *Notifications* - View alerts for detected events\n"
        "• 🧰 *Tools* - Manage keywords and objects for detection\n\n"
        "Use the menu buttons to navigate through features."
    )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /getid command."""
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    
    id_message = f"Your chat ID is: `{chat_id}`\n\nUse this ID to set up notifications in the monitoring system."
    
    if session.get('logged_in', False):
        # Update user's telegram chat_id in the system
        data = {
            'telegram_chat_id': str(chat_id),
            'receive_updates': True
        }
        response = await api_request('post', 'user/telegram', data, session.get('session_id'))
        
        if 'error' not in response:
            id_message += "\n\n✅ Your chat ID has been linked to your account!"
    
    await update.message.reply_text(id_message, parse_mode=ParseMode.MARKDOWN)

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /logout command."""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        if session.get('logged_in'):
            # Call logout API
            await api_request('post', 'logout', session_id=session.get('session_id'))
        
        # Clear session
        user_sessions[user_id] = {'logged_in': False}
        save_sessions()
        
        await update.message.reply_text(
            "You have been logged out successfully.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login Again", callback_data="login")]
            ])
        )
    else:
        await update.message.reply_text("You were not logged in.")

# Message Handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from the main menu and submenus."""
    user_id = update.effective_user.id
    text = update.message.text
    session = user_sessions.get(user_id, {})
    
    if not session.get('logged_in', False):
        await update.message.reply_text(
            "Please login first. Use /start to begin.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login", callback_data="login")]
            ])
        )
        return
    
    # Main menu options
    if text == "📺 Streams":
        await update.message.reply_text(
            "Select a streams option:",
            reply_markup=get_streams_keyboard()
        )
    elif text == "🔍 Detection Status":
        await show_detection_status(update, user_id, session.get('session_id'))
    elif text == "🔔 Notifications":
        await show_notifications(update, user_id, session.get('session_id'))
    elif text == "🧰 Tools":
        await update.message.reply_text(
            "Select a tools option:",
            reply_markup=get_tools_keyboard()
        )
    # Streams submenu
    elif text == "🟢 My Streams":
        await show_my_streams(update, user_id, session.get('session_id'))
    elif text == "➕ Add Stream":
        await update.message.reply_text(
            "Enter the stream room URL (e.g., https://chaturbate.com/username/):",
            reply_markup=get_back_keyboard()
        )
        return ADD_STREAM_URL
    # Tools submenu
    elif text == "📝 Keywords":
        await show_keywords(update, user_id, session.get('session_id'))
    elif text == "🎯 Objects":
        await show_objects(update, user_id, session.get('session_id'))
    elif text == "🔙 Back to Main Menu":
        await update.message.reply_text(
            "Returned to main menu.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "Unknown command. Please use the menu options.",
            reply_markup=get_main_keyboard()
        )

# Conversation Handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Ensure user has a session
    if user_id not in user_sessions:
        user_sessions[user_id] = {'logged_in': False}
        save_sessions()
    
    if query.data == "login":
        # Check if already logged in
        session = user_sessions.get(user_id, {})
        if session.get('logged_in', False):
            response = await api_request('get', 'agent/dashboard', session_id=session.get('session_id'))
            if 'error' not in response:
                await query.edit_message_text(
                    "You're already logged in! Use the menu to continue.",
                    reply_markup=get_main_keyboard()
                )
                return ConversationHandler.END
        
        await query.edit_message_text(
            "Please enter your username or email to login:"
        )
        return LOGIN
    
    elif query.data.startswith("stream_"):
        stream_id = query.data.split("_")[1]
        await show_stream_details(query, user_id, stream_id, session.get('session_id'))
    
    elif query.data.startswith("start_") or query.data.startswith("stop_"):
        action = "stop" if query.data.startswith("stop_") else "start"
        stream_id = query.data.split("_")[1]
        await trigger_detection(query, user_id, stream_id, action, session.get('session_id'))
    
    elif query.data.startswith("notification_"):
        notification_id = query.data.split("_")[1]
        await mark_notification_read(query, user_id, notification_id, session.get('session_id'))
    
    elif query.data == "read_all_notifications":
        await mark_all_notifications_read(query, user_id, session.get('session_id'))
    
    return ConversationHandler.END

async def login_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle login conversation."""
    user_id = update.effective_user.id
    message = update.message.text
    
    # Store username and ask for password
    user_sessions[user_id]['username'] = message
    save_sessions()
    
    await update.message.reply_text(
        "Please enter your password:"
    )
    return PASSWORD

async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle password input."""
    user_id = update.effective_user.id
    password = update.message.text
    username = user_sessions[user_id].get('username', '')
    
    # For security, delete the password message
    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Error deleting password message: {str(e)}")
    
    # Attempt login
    data = {
        'username': username,
        'password': password
    }
    response = await api_request('post', 'api/login', data)
    
    if 'error' in response or response.get('message') != "Login successful":
        await update.message.reply_text(
            f"Login failed: {response.get('error', response.get('message', 'Invalid credentials'))}\nPlease try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Try Again", callback_data="login")]
            ])
        )
        return ConversationHandler.END
    
    # Store session details
    session_id = response.get('session_id')  # Note: Adjust based on actual API response; currently using cookies
    user_sessions[user_id] = {
        'logged_in': True,
        'username': response.get('username'),
        'role': response.get('role'),
        'telegram_username': response.get('telegram_username'),
        'telegram_chat_id': response.get('telegram_chat_id'),
        'session_id': update.message.chat_id  # Store chat_id as session_id placeholder
    }
    save_sessions()
    
    await update.message.reply_text(
        "✅ Login successful! Use the menu to manage your streams and notifications.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def add_stream_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle stream URL input."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    if not session.get('logged_in', False):
        await update.message.reply_text(
            "Please login first. Use /start to begin.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login", callback_data="login")]
            ])
        )
        return ConversationHandler.END
    
    text = update.message.text
    if text == "🔙 Back to Main Menu":
        await update.message.reply_text(
            "Returned to main menu.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    user_sessions[user_id]['stream_url'] = text
    save_sessions()
    
    await update.message.reply_text(
        "Select the platform for the stream:",
        reply_markup=get_platform_keyboard()
    )
    return ADD_STREAM_PLATFORM

async def add_stream_platform(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle platform selection."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    if not session.get('logged_in', False):
        await update.message.reply_text(
            "Please login first. Use /start to begin.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login", callback_data="login")]
            ])
        )
        return ConversationHandler.END
    
    text = update.message.text
    if text == "🔙 Cancel":
        await update.message.reply_text(
            "Stream creation cancelled.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    if text not in ["Chaturbate", "Stripchat"]:
        await update.message.reply_text(
            "Please select a valid platform (Chaturbate or Stripchat).",
            reply_markup=get_platform_keyboard()
        )
        return ADD_STREAM_PLATFORM
    
    user_sessions[user_id]['platform'] = text.lower()
    save_sessions()
    
    # Fetch agents
    response = await api_request('get', 'agents', session_id=session.get('session_id'))
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to fetch agents: {response['error']}",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    agents = response
    if not agents:
        await update.message.reply_text(
            "No agents available. Creating stream without agent assignment.",
            reply_markup=get_back_keyboard()
        )
        user_sessions[user_id]['agent_id'] = None
        save_sessions()
        return await create_stream(update, context)
    
    agent_list = "\n".join([f"{agent['id']}: {agent['username']}" for agent in agents])
    await update.message.reply_text(
        f"Enter the agent ID to assign the stream (or type 'none' for no assignment):\n{agent_list}",
        reply_markup=get_back_keyboard()
    )
    return ADD_STREAM_AGENT

async def add_stream_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle agent ID input."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    if not session.get('logged_in', False):
        await update.message.reply_text(
            "Please login first. Use /start to begin.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login", callback_data="login")]
            ])
        )
        return ConversationHandler.END
    
    text = update.message.text
    if text == "🔙 Back to Main Menu":
        await update.message.reply_text(
            "Returned to main menu.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    if text.lower() == 'none':
        user_sessions[user_id]['agent_id'] = None
        save_sessions()
        return await create_stream(update, context)
    
    try:
        agent_id = int(text)
        response = await api_request('get', 'agents', session_id=session.get('session_id'))
        if 'error' in response:
            await update.message.reply_text(
                f"Failed to verify agent: {response['error']}",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        agents = response
        if not any(agent['id'] == agent_id for agent in agents):
            await update.message.reply_text(
                "Invalid agent ID. Please enter a valid ID or 'none'.",
                reply_markup=get_back_keyboard()
            )
            return ADD_STREAM_AGENT
        
        user_sessions[user_id]['agent_id'] = agent_id
        save_sessions()
        return await create_stream(update, context)
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid agent ID (number) or 'none'.",
            reply_markup=get_back_keyboard()
        )
        return ADD_STREAM_AGENT

async def create_stream(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create the stream via API."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {})
    session_id = session.get('session_id')
    room_url = session.get('stream_url')
    platform = session.get('platform')
    agent_id = session.get('agent_id')
    
    data = {
        'room_url': room_url,
        'platform': platform,
        'agent_id': agent_id
    }
    
    response = await api_request('post', 'streams', data, session_id)
    
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to create stream: {response['error']}",
            reply_markup=get_main_keyboard()
        )
    else:
        stream = response.get('stream', {})
        await update.message.reply_text(
            f"✅ Stream created successfully!\n"
            f"ID: {stream.get('id')}\n"
            f"URL: {stream.get('room_url')}\n"
            f"Platform: {stream.get('type')}",
            reply_markup=get_main_keyboard()
        )
    
    # Clear temporary session data
    user_sessions[user_id].pop('stream_url', None)
    user_sessions[user_id].pop('platform', None)
    user_sessions[user_id].pop('agent_id', None)
    save_sessions()
    
    return ConversationHandler.END

# Utility Functions
async def show_my_streams(update: Update, user_id: int, session_id: str) -> None:
    """Show the user's assigned streams."""
    response = await api_request('get', 'agent/dashboard', session_id=session_id)
    
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to fetch streams: {response['error']}",
            reply_markup=get_streams_keyboard()
        )
        return
    
    streams = response.get('assignments', [])
    if not streams:
        await update.message.reply_text(
            "You have no assigned streams.",
            reply_markup=get_streams_keyboard()
        )
        return
    
    streams_text = "*Your Assigned Streams*\n\n"
    stream_buttons = []
    
    for stream in streams:
        status = "🟢" if stream.get('status') == 'online' else "⚫"
        stream_id = stream.get('id')
        streams_text += f"{status} Stream #{stream_id}: {stream.get('streamer_username', 'Unnamed')} ({stream.get('type')})\n"
        stream_buttons.append([InlineKeyboardButton(
            f"{status} Stream #{stream_id}", 
            callback_data=f"stream_{stream_id}"
        )])
    
    await update.message.reply_text(
        streams_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(stream_buttons)
    )

async def show_stream_details(query, user_id: int, stream_id: str, session_id: str) -> None:
    """Show details of a specific stream."""
    response = await api_request('get', f'detection-status/{stream_id}', session_id=session_id)
    
    if 'error' in response:
        await query.edit_message_text(f"Error getting stream details: {response['error']}")
        return
    
    stream_status = "🟢 Active" if response.get('active', False) else "⚫ Inactive"
    stream_url = response.get('stream_url', 'N/A')
    
    # Create control buttons
    control_buttons = []
    if response.get('active', False):
        control_buttons.append(InlineKeyboardButton("⏹️ Stop Monitoring", callback_data=f"stop_{stream_id}"))
    else:
        control_buttons.append(InlineKeyboardButton("▶️ Start Monitoring", callback_data=f"start_{stream_id}"))
    
    status_message = (
        f"*Stream #{stream_id} Details*\n\n"
        f"• Status: {stream_status}\n"
        f"• URL: `{stream_url}`\n"
        f"• Type: {response.get('platform', 'Unknown')}\n"
        f"• Last updated: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    await query.edit_message_text(
        status_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            control_buttons,
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"stream_{stream_id}")],
            [InlineKeyboardButton("🔙 Back to Streams", callback_data="streams_list")]
        ])
    )

async def trigger_detection(query, user_id: int, stream_id: str, action: str, session_id: str) -> None:
    """Start or stop detection for a stream."""
    data = {
        'stream_id': int(stream_id),
        'stop': action == "stop"
    }
    
    response = await api_request('post', 'trigger-detection', data, session_id)
    
    if 'error' in response:
        await query.edit_message_text(f"Error controlling monitoring: {response['error']}")
        return
    
    status = "stopped" if action == "stop" else "started"
    await query.edit_message_text(
        f"✅ Monitoring {status} successfully for Stream #{stream_id}.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Stream", callback_data=f"stream_{stream_id}")]
        ])
    )

async def show_detection_status(update: Update, user_id: int, session_id: str) -> None:
    """Show detection status for all assigned streams."""
    response = await api_request('get', 'agent/dashboard', session_id=session_id)
    
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to fetch detection status: {response['error']}",
            reply_markup=get_main_keyboard()
        )
        return
    
    streams = response.get('assignments', [])
    if not streams:
        await update.message.reply_text(
            "You have no assigned streams to monitor.",
            reply_markup=get_main_keyboard()
        )
        return
    
    status_text = "*Detection Status*\n\n"
    for stream in streams:
        stream_id = stream.get('id')
        status_response = await api_request('get', f'detection-status/{stream_id}', session_id=session_id)
        if 'error' in status_response:
            status_text += f"Stream #{stream_id}: Error - {status_response['error']}\n"
        else:
            status = "🟢 Active" if status_response.get('active', False) else "⚫ Inactive"
            status_text += f"Stream #{stream_id}: {status} ({stream.get('streamer_username', 'Unnamed')})\n"
    
    await update.message.reply_text(
        status_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def show_notifications(update: Update, user_id: int, session_id: str) -> None:
    """Show notifications for the user."""
    response = await api_request('get', 'notifications', session_id=session_id)
    
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to fetch notifications: {response['error']}",
            reply_markup=get_main_keyboard()
        )
        return
    
    notifications = response
    if not notifications:
        await update.message.reply_text(
            "You have no notifications.",
            reply_markup=get_main_keyboard()
        )
        return
    
    unread_count = sum(1 for n in notifications if not n.get('read', False))
    notifications_text = f"*Your Notifications* ({unread_count} unread)\n\n"
    notification_buttons = []
    
    for notification in notifications[:5]:
        notification_id = notification.get('id')
        read_status = "✓" if notification.get('read', False) else "🔴"
        timestamp = notification.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime("%m-%d %H:%M")
            except:
                pass
        
        notifications_text += f"{read_status} #{notification_id}: {notification.get('event_type')} ({timestamp})\n"
        
        if not notification.get('read', False):
            notification_buttons.append([InlineKeyboardButton(
                f"Mark #{notification_id} as Read", 
                callback_data=f"notification_{notification_id}"
            )])
    
    if unread_count > 0:
        notification_buttons.append([InlineKeyboardButton("📖 Mark All as Read", callback_data="read_all_notifications")])
    
    await update.message.reply_text(
        notifications_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(notification_buttons)
    )

async def mark_notification_read(query, user_id: int, notification_id: str, session_id: str) -> None:
    """Mark a notification as read."""
    response = await api_request('put', f'notifications/{notification_id}/read', session_id=session_id)
    
    if 'error' in response:
        await query.edit_message_text(f"Error marking notification as read: {response['error']}")
    else:
        await query.edit_message_text(
            f"✅ Notification #{notification_id} marked as read.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Notifications", callback_data="notifications_list")]
            ])
        )

async def mark_all_notifications_read(query, user_id: int, session_id: str) -> None:
    """Mark all notifications as read."""
    response = await api_request('put', 'notifications/read-all', session_id=session_id)
    
    if 'error' in response:
        await query.edit_message_text(f"Error marking notifications as read: {response['error']}")
    else:
        await query.edit_message_text(
            "✅ All notifications marked as read.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Notifications", callback_data="notifications_list")]
            ])
        )

async def show_keywords(update: Update, user_id: int, session_id: str) -> None:
    """Show list of monitored keywords."""
    response = await api_request('get', 'keywords', session_id=session_id)
    
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to fetch keywords: {response['error']}",
            reply_markup=get_tools_keyboard()
        )
        return
    
    keywords = response
    if not keywords:
        await update.message.reply_text(
            "No keywords found in the system.",
            reply_markup=get_tools_keyboard()
        )
        return
    
    keywords_text = f"*Monitored Keywords* ({len(keywords)})\n\n"
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        keywords_text += "• " + ", ".join(item.get('keyword', 'Unknown') for item in batch) + "\n"
    
    await update.message.reply_text(
        keywords_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_tools_keyboard()
    )

async def show_objects(update: Update, user_id: int, session_id: str) -> None:
    """Show list of monitored objects."""
    response = await api_request('get', 'objects', session_id=session_id)
    
    if 'error' in response:
        await update.message.reply_text(
            f"Failed to fetch objects: {response['error']}",
            reply_markup=get_tools_keyboard()
        )
        return
    
    objects = response
    if not objects:
        await update.message.reply_text(
            "No objects found in the system.",
            reply_markup=get_tools_keyboard()
        )
        return
    
    objects_text = f"*Monitored Objects* ({len(objects)})\n\n"
    for i in range(0, len(objects), 5):
        batch = objects[i:i+5]
        objects_text += "• " + ", ".join(item.get('object_name', 'Unknown') for item in batch) + "\n"
    
    await update.message.reply_text(
        objects_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_tools_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    await update.message.reply_text(
        "Operation cancelled.",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

async def main():
    """Main function to run the Telegram bot."""
    try:
        token = TELEGRAM_TOKEN
        if not token:
            logger.error("TELEGRAM_TOKEN not set in environment variables")
            return
        
        # Create the Application
        application = Application.builder().token(token).build()

        # Define conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(button_callback, pattern="^login$"),
                MessageHandler(filters.Regex("^(➕ Add Stream)$"), handle_message)
            ],
            states={
                LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_conversation)],
                PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler)],
                ADD_STREAM_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stream_url)],
                ADD_STREAM_PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stream_platform)],
                ADD_STREAM_AGENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stream_agent)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )

        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("getid", getid))
        application.add_handler(CommandHandler("logout", logout))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(button_callback))

        # Start the bot
        logger.info("Telegram bot starting")
        
        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for s in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown(application)))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Telegram bot started successfully")
        
        # Keep running until stopped
        stop_signal = asyncio.Future()
        await stop_signal
    
    except Exception as e:
        logger.error(f"Telegram bot error: {str(e)}")

async def shutdown(application):
    """Shut down the application gracefully."""
    logger.info("Shutting down...")
    save_sessions()
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()

def run_bot():
    """Run the bot in the event loop."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Telegram bot stopped by user")
    except asyncio.CancelledError:
        logger.info("Telegram bot tasks cancelled")
    except Exception as e:
        logger.error(f"Telegram bot error in event loop: {str(e)}")

if __name__ == "__main__":
    run_bot()