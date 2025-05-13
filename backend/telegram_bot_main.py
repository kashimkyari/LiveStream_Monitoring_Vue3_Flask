import os
import asyncio
import logging
import signal
import json
import requests
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Configure logging to match Flask app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'https://monitor-backend.jetcamstudio.com:5000')
API_ADMIN_TOKEN = os.getenv('API_ADMIN_TOKEN', '')

# Conversation states
REGISTER, LOGIN, PASSWORD, EMAIL, CHATID, STREAM_URL, KEYWORD, OBJECT_NAME = range(8)

# User session data
user_sessions = {}

# Define keyboard layouts
def get_main_keyboard():
    """Create the main menu keyboard."""
    keyboard = [
        ["📺 Streams", "🔍 Detection Status"],
        ["🏆 Achievements", "🔔 Notifications"],
        ["🧰 Tools", "ℹ️ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_tools_keyboard():
    """Create the tools submenu keyboard."""
    keyboard = [
        ["📝 Keywords", "🎯 Objects"],
        ["📊 My Stats", "🆔 Get My ID"],
        ["🔙 Back to Main Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_streams_keyboard():
    """Create the streams submenu keyboard."""
    keyboard = [
        ["🟢 My Streams", "➕ Add Stream"],
        ["⚙️ Manage Streams", "📊 Stream Analytics"],
        ["🔙 Back to Main Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_achievements_keyboard():
    """Create the achievements submenu keyboard."""
    keyboard = [
        ["🏅 My Badges", "📈 Leaderboard"],
        ["🎯 Challenges", "🔥 Streaks"],
        ["🔙 Back to Main Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Create a simple back button keyboard."""
    keyboard = [["🔙 Back to Main Menu"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# API Helper Functions
async def api_request(method, endpoint, data=None, token=None, params=None):
    """Make a request to the API."""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if token:
        headers['Authorization'] = f"Bearer {token}"
    
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method.lower() == 'put':
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return {'error': 'Invalid HTTP method'}
        
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return response.json()
            except:
                return {'message': response.text}
        else:
            return {'error': f"API Error ({response.status_code}): {response.text}"}
    
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return {'error': f"Connection error: {str(e)}"}

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    user = update.effective_user
    user_id = user.id
    
    # Reset session data for this user
    user_sessions[user_id] = {'registered': False, 'logged_in': False}
    
    welcome_message = (
        f"👋 Welcome, {user.first_name}! I'm your LiveStream Monitoring Bot.\n\n"
        "I can help you monitor streams, detect content, and get notifications when events occur.\n\n"
    )
    
    # Check if user has registered with the system
    login_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Login", callback_data="login")],
        [InlineKeyboardButton("📝 Register", callback_data="register")]
    ])
    
    await update.message.reply_text(
        welcome_message + "Please login or register to access all features:", 
        reply_markup=login_keyboard
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
        "• 📺 *Streams* - Manage and monitor your streams\n"
        "• 🔍 *Detection Status* - Check current detection status\n"
        "• 🏆 *Achievements* - View your badges and leaderboard\n"
        "• 🔔 *Notifications* - View your alerts and notifications\n"
        "• 🧰 *Tools* - Access keywords, objects, and utilities\n\n"
        "*Achievement System:*\n"
        "Earn points and badges by:\n"
        "• 🔎 Detecting content correctly\n"
        "• ⏱ Responding quickly to alerts\n"
        "• 📆 Maintaining daily streaks\n"
        "• 🏅 Completing challenges\n\n"
        "Use the menu buttons to navigate through different features."
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
        response = await api_request('post', 'user/telegram', data, session.get('token'))
        
        if 'error' not in response:
            id_message += "\n\n✅ Your chat ID has been automatically linked to your account!"
    
    await update.message.reply_text(id_message, parse_mode=ParseMode.MARKDOWN)

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /logout command."""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        session = user_sessions[user_id]
        if session.get('token'):
            # Call logout API
            await api_request('post', 'logout', token=session.get('token'))
        
        # Clear session
        user_sessions[user_id] = {'registered': False, 'logged_in': False}
        
        await update.message.reply_text(
            "You have been logged out successfully.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login Again", callback_data="login")]
            ])
        )
    else:
        await update.message.reply_text("You were not logged in.")

# Login and Registration Handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Ensure user has a session
    if user_id not in user_sessions:
        user_sessions[user_id] = {'registered': False, 'logged_in': False}
    
    if query.data == "login":
        await query.edit_message_text(
            "Please enter your username or email to login:"
        )
        return LOGIN
    
    elif query.data == "register":
        await query.edit_message_text(
            "Let's create your account.\n\nPlease enter a username (3-20 characters):"
        )
        return REGISTER
    
    elif query.data.startswith("stream_"):
        stream_id = query.data.split("_")[1]
        
        # Get session token
        session = user_sessions.get(user_id, {})
        token = session.get('token')
        
        if not token:
            await query.edit_message_text("Please login first. Use /start to begin.")
            return ConversationHandler.END
        
        # Get stream details
        response = await api_request('get', f'detection-status/{stream_id}', token=token)
        
        if 'error' in response:
            await query.edit_message_text(f"Error getting stream details: {response['error']}")
            return ConversationHandler.END
        
        stream_status = "🟢 Active" if response.get('active', False) else "⚫ Inactive"
        stream_url = response.get('stream_url', 'N/A')
        
        # Create control buttons
        control_buttons = []
        if response.get('active', False):
            control_buttons.append(InlineKeyboardButton("⏹️ Stop Detection", callback_data=f"stop_{stream_id}"))
        else:
            control_buttons.append(InlineKeyboardButton("▶️ Start Detection", callback_data=f"start_{stream_id}"))
        
        status_message = (
            f"*Stream #{stream_id} Details*\n\n"
            f"• Status: {stream_status}\n"
            f"• URL: `{stream_url}`\n"
            f"• Type: {response.get('stream_type', 'Unknown')}\n"
            f"• Detections: {response.get('detection_count', 0)}\n\n"
            f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
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
    
    elif query.data.startswith("start_") or query.data.startswith("stop_"):
        action = "stop" if query.data.startswith("stop_") else "start"
        stream_id = query.data.split("_")[1]
        
        # Get session token
        session = user_sessions.get(user_id, {})
        token = session.get('token')
        
        if not token:
            await query.edit_message_text("Please login first. Use /start to begin.")
            return ConversationHandler.END
        
        # Trigger detection
        response = await api_request('post', 'trigger-detection', 
                                    data={'stream_id': int(stream_id), 'stop': action == "stop"},
                                    token=token)
        
        if 'error' in response:
            await query.edit_message_text(f"Error controlling detection: {response['error']}")
            return ConversationHandler.END
        
        status = "stopped" if action == "stop" else "started"
        await query.edit_message_text(
            f"Detection {status} successfully for Stream #{stream_id}.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Stream", callback_data=f"stream_{stream_id}")]
            ])
        )
    
    elif query.data == "streams_list":
        await show_streams_list(query, user_id)
    
    elif query.data == "my_achievements":
        await show_achievements(query, user_id)
    
    elif query.data == "read_all_notifications":
        # Mark all notifications as read
        session = user_sessions.get(user_id, {})
        token = session.get('token')
        
        if not token:
            await query.edit_message_text("Please login first. Use /start to begin.")
            return ConversationHandler.END
        
        response = await api_request('put', 'agent/notifications/read-all', token=token)
        
        if 'error' in response:
            await query.edit_message_text(f"Error marking notifications as read: {response['error']}")
        else:
            count = response.get('count', 0)
            await query.edit_message_text(
                f"✅ Marked {count} notifications as read.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Notifications", callback_data="notifications_list")]
                ])
            )
    
    elif query.data == "notifications_list":
        await show_notifications(query, user_id)
    
    elif query.data.startswith("notification_"):
        notification_id = query.data.split("_")[1]
        session = user_sessions.get(user_id, {})
        token = session.get('token')
        
        if not token:
            await query.edit_message_text("Please login first. Use /start to begin.")
            return ConversationHandler.END
        
        # Mark notification as read
        response = await api_request('put', f'agent/notifications/{notification_id}/read', token=token)
        
        if 'error' in response:
            await query.edit_message_text(f"Error marking notification as read: {response['error']}")
        else:
            await query.edit_message_text(
                f"✅ Notification #{notification_id} marked as read.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Notifications", callback_data="notifications_list")]
                ])
            )
    
    elif query.data == "keywords_list":
        await show_keywords(query, user_id)
    
    elif query.data == "objects_list":
        await show_objects(query, user_id)
    
    elif query.data == "my_stats":
        await show_agent_stats(query, user_id)
    
    return ConversationHandler.END

async def show_streams_list(query, user_id):
    """Show list of streams for the user."""
    session = user_sessions.get(user_id, {})
    token = session.get('token')
    
    if not token:
        await query.edit_message_text("Please login first. Use /start to begin.")
        return
    
    # Get agent dashboard data
    response = await api_request('get', 'agent/dashboard', token=token)
    
    if 'error' in response:
        await query.edit_message_text(f"Error fetching streams: {response['error']}")
        return
    
    # Format streams list
    ongoing = response.get('ongoing_streams', 0)
    assignments = response.get('assignments', [])
    
    if not assignments:
        await query.edit_message_text(
            "You don't have any streams assigned to you yet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="streams_list")]
            ])
        )
        return
    
    streams_text = f"*Your Assigned Streams* ({ongoing} ongoing)\n\n"
    stream_buttons = []
    
    for assignment in assignments:
        stream = assignment.get('stream', {})
        stream_id = stream.get('id')
        status = "🟢" if stream.get('active', False) else "⚫"
        streams_text += f"{status} Stream #{stream_id}: {stream.get('name', 'Unnamed')}\n"
        stream_buttons.append([InlineKeyboardButton(
            f"{status} Stream #{stream_id}", 
            callback_data=f"stream_{stream_id}"
        )])
    
    stream_buttons.append([InlineKeyboardButton("🔄 Refresh List", callback_data="streams_list")])
    
    await query.edit_message_text(
        streams_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(stream_buttons)
    )

async def show_notifications(query, user_id):
    """Show list of notifications for the user."""
    session = user_sessions.get(user_id, {})
    token = session.get('token')
    
    if not token:
        await query.edit_message_text("Please login first. Use /start to begin.")
        return
    
    # Get notifications
    response = await api_request('get', 'agent/notifications', token=token)
    
    if 'error' in response:
        await query.edit_message_text(f"Error fetching notifications: {response['error']}")
        return
    
    notifications = response.get('notifications', [])
    
    if not notifications:
        await query.edit_message_text(
            "You don't have any notifications.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="notifications_list")]
            ])
        )
        return
    
    # Count unread notifications
    unread_count = sum(1 for n in notifications if not n.get('read', False))
    
    notifications_text = f"*Your Notifications* ({unread_count} unread)\n\n"
    notification_buttons = []
    
    # Show only the most recent 5 notifications
    for notification in notifications[:5]:
        notification_id = notification.get('id')
        read_status = "✓" if notification.get('read', False) else "🔴"
        timestamp = notification.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
                timestamp = dt.strftime("%m-%d %H:%M")
            except:
                pass
        
        notifications_text += f"{read_status} #{notification_id}: {notification.get('message', 'No message')} ({timestamp})\n"
        
        if not notification.get('read', False):
            notification_buttons.append([InlineKeyboardButton(
                f"Mark #{notification_id} as Read", 
                callback_data=f"notification_{notification_id}"
            )])
    
    if unread_count > 0:
        notification_buttons.append([InlineKeyboardButton("📖 Mark All as Read", callback_data="read_all_notifications")])
    
    notification_buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="notifications_list")])
    
    await query.edit_message_text(
        notifications_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(notification_buttons)
    )

async def show_keywords(query, user_id):
    """Show list of keywords for monitoring."""
    session = user_sessions.get(user_id, {})
    token = session.get('token')
    
    if not token:
        await query.edit_message_text("Please login first. Use /start to begin.")
        return
    
    # Get keywords
    response = await api_request('get', 'keywords', token=token)
    
    if 'error' in response:
        await query.edit_message_text(f"Error fetching keywords: {response['error']}")
        return
    
    keywords = response
    
    if not keywords:
        await query.edit_message_text(
            "No keywords found in the system.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="keywords_list")]
            ])
        )
        return
    
    keywords_text = f"*Monitored Keywords* ({len(keywords)})\n\n"
    
    # Group keywords in batches of 5 to make it readable
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        keywords_text += "• " + ", ".join(item.get('keyword', 'Unknown') for item in batch) + "\n"
    
    await query.edit_message_text(
        keywords_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="keywords_list")]
        ])
    )

async def show_objects(query, user_id):
    """Show list of objects for monitoring."""
    session = user_sessions.get(user_id, {})
    token = session.get('token')
    
    if not token:
        await query.edit_message_text("Please login first. Use /start to begin.")
        return
    
    # Get objects
    response = await api_request('get', 'objects', token=token)
    
    if 'error' in response:
        await query.edit_message_text(f"Error fetching objects: {response['error']}")
        return
    
    objects = response
    
    if not objects:
        await query.edit_message_text(
            "No objects found in the system.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="objects_list")]
            ])
        )
        return
    
    objects_text = f"*Monitored Objects* ({len(objects)})\n\n"
    
    # Group objects in batches of 5 to make it readable
    for i in range(0, len(objects), 5):
        batch = objects[i:i+5]
        objects_text += "• " + ", ".join(item.get('object_name', 'Unknown') for item in batch) + "\n"
    
    await query.edit_message_text(
        objects_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="objects_list")]
        ])
    )

async def show_agent_stats(query, user_id):
    """Show agent performance statistics."""
    session = user_sessions.get(user_id, {})
    token = session.get('token')
    
    if not token:
        await query.edit_message_text("Please login first. Use /start to begin.")
        return
    
    # Get agent performance stats
    response = await api_request('get', 'analytics/agent-performance', token=token)
    
    if 'error' in response:
        await query.edit_message_text(f"Error fetching stats: {response['error']}")
        return
    
    resolution_rate = response.get('resolutionRate', 0)
    avg_response_time = response.get('avgResponseTime', 0)
    detection_breakdown = response.get('detectionBreakdown', [])
    activity_timeline = response.get('activityTimeline', [])
    
    # Calculate XP and level based on activity
    total_detections = sum(item.get('count', 0) for item in detection_breakdown)
    xp = total_detections * 10 + resolution_rate * 5
    level = 1 + (xp // 100)
    next_level_xp = (level) * 100
    xp_progress = xp % 100
    
    stats_text = (
        f"*Your Agent Stats* (Level {level})\n\n"
        f"• XP: {xp} ({xp_progress}% to Level {level+1})\n"
        f"• Resolution Rate: {resolution_rate}%\n"
        f"• Avg Response Time: {avg_response_time:.1f} min\n\n"
        f"*Detection Breakdown:*\n"
    )
    
    # Add detection breakdown
    for item in detection_breakdown:
        stats_text += f"• {item.get('type', 'Unknown')}: {item.get('count', 0)}\n"
    
    # Add achievements
    stats_text += "\n*Recent Achievements:*\n"
    
    # Generate some fake achievements based on stats
    achievements = []
    if resolution_rate > 90:
        achievements.append("🏆 Quick Responder")
    if total_detections > 50:
        achievements.append("🔍 Eagle Eye")
    if avg_response_time < 5:
        achievements.append("⚡ Lightning Fast")
    
    if achievements:
        for achievement in achievements:
            stats_text += f"• {achievement}\n"
    else:
        stats_text += "• No achievements yet. Keep monitoring!\n"
    
    await query.edit_message_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Stats", callback_data="my_stats")]
        ])
    )

async def show_achievements(query, user_id):
    """Show user achievements and gamification status."""
    session = user_sessions.get(user_id, {})
    token = session.get('token')
    
    if not token:
        await query.edit_message_text("Please login first. Use /start to begin.")
        return
    
    # Get agent performance stats for basing achievements on
    response = await api_request('get', 'analytics/agent-performance', token=token)
    
    if 'error' in response:
        await query.edit_message_text(f"Error fetching achievements: {response['error']}")
        return
    
    # Extract data for gamification
    resolution_rate = response.get('resolutionRate', 0)
    avg_response_time = response.get('avgResponseTime', 0)
    detection_breakdown = response.get('detectionBreakdown', [])
    activity_timeline = response.get('activityTimeline', [])
    
    # Calculate XP and level
    total_detections = sum(item.get('count', 0) for item in detection_breakdown)
    xp = total_detections * 10 + resolution_rate * 5
    level = 1 + (xp // 100)
    next_level_xp = (level) * 100
    xp_progress = xp % 100
    
    # Create progress bar for XP
    progress_bar = "["
    progress_blocks = int(xp_progress / 10)
    for i in range(10):
        if i < progress_blocks:
            progress_bar += "█"
        else:
            progress_bar += "▒"
    progress_bar += "]"
    
    # Generate badges based on metrics
    badges = []
    
    if resolution_rate > 90:
        badges.append("🏆 Quick Responder")
    if total_detections > 50:
        badges.append("🔍 Eagle Eye")
    if avg_response_time < 5:
        badges.append("⚡ Lightning Fast")
    if len(activity_timeline) > 7:
        badges.append("📆 Weekly Warrior")
    if total_detections > 100:
        badges.append("💯 Century Club")
    
    # Daily streak
    streak_days = min(len(activity_timeline), 30)
    
    achievements_text = (
        f"*Your Achievements*\n\n"
        f"👤 Level {level} Monitor\n"
        f"⭐ XP: {xp}/{next_level_xp} {progress_bar}\n"
        f"🔥 Daily Streak: {streak_days} days\n\n"
        f"*Badges Earned:*\n"
    )
    
    if badges:
        for badge in badges:
            achievements_text += f"• {badge}\n"
    else:
        achievements_text += "• No badges yet. Keep monitoring!\n"
    
    # Add challenges
    achievements_text += "\n*Current Challenges:*\n"
    
    challenges = [
        f"• 🎯 Respond to 5 more alerts (Progress: {min(5, total_detections)}/5)",
        f"• 🔍 Find 3 objects in streams (Progress: {min(3, total_detections//2)}/3)",
        f"• ⏱ Maintain < 2 min response time for a day"
    ]
    
    for challenge in challenges:
        achievements_text += f"{challenge}\n"
    
    await query.edit_message_text(
        achievements_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Stats", callback_data="my_stats")],
            [InlineKeyboardButton("🏅 View Leaderboard", callback_data="leaderboard")]
        ])
    )

async def login_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle login conversation."""
    user_id = update.effective_user.id
    message = update.message.text
    
    # Store username and ask for password
    user_sessions[user_id]['username'] = message
    
    await update.message.reply_text(
        "Please enter your password:"
    )
    return PASSWORD

async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle password input."""
    user_id = update.effective_user.id
    password = update.message.text
    username = user_sessions[user_id].get('username', '')
    
    # For security, delete the message with the password if possible
    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Error deleting password message: {str(e)}")
    
    # Attempt login
import os
import asyncio
import logging
import signal
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Configure logging to match Flask app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define keyboard layouts
def get_main_keyboard():
    """Create the main menu keyboard."""
    keyboard = [
        ["📺 Check Stream Status", "🔔 Set Notifications"],
        ["ℹ️ Help", "🆔 Get My ID"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    user_name = update.effective_user.first_name
    welcome_message = (
        f"👋 Welcome, {user_name}! I'm your LiveStream Monitoring Bot.\n\n"
        "I can help you monitor your streams and send notifications when status changes.\n\n"
        "Use the buttons below to interact with me:"
    )
    await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /help command."""
    help_text = (
        "🔹 *LiveStream Monitoring Bot Help* 🔹\n\n"
        "*Commands:*\n"
        "• /start - Start the bot and show main menu\n"
        "• /help - Show this help message\n"
        "• /getid - Get your chat ID for notifications\n\n"
        "*Buttons:*\n"
        "• 📺 Check Stream Status - View current stream status\n"
        "• 🔔 Set Notifications - Configure your notification preferences\n"
        "• ℹ️ Help - Show this help message\n"
        "• 🆔 Get My ID - Get your chat ID for notifications"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /getid command."""
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: `{chat_id}`\n\nUse this ID to set up notifications in the monitoring system.", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages and keyboard button clicks."""
    text = update.message.text
    
    if text == "📺 Check Stream Status":
        # This would connect to your monitoring system
        await update.message.reply_text(
            "🔄 Checking stream status...\n\n"
            "This feature will connect to your monitoring system to show current stream status.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Refresh Status", callback_data="refresh_status")]
            ])
        )
    
    elif text == "🔔 Set Notifications":
        # Notification settings
        notification_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Enable All", callback_data="enable_all")],
            [InlineKeyboardButton("⚠️ Errors Only", callback_data="errors_only")],
            [InlineKeyboardButton("❌ Disable All", callback_data="disable_all")]
        ])
        await update.message.reply_text(
            "Choose your notification preferences:",
            reply_markup=notification_keyboard
        )
    
    elif text == "ℹ️ Help":
        await help_command(update, context)
    
    elif text == "🆔 Get My ID":
        await getid(update, context)
    
    else:
        await update.message.reply_text(
            "Please use the menu buttons to interact with me.",
            reply_markup=get_main_keyboard()
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()  # Answer the callback query
    
    if query.data == "refresh_status":
        await query.edit_message_text(
            "🔄 Updated status: All systems operational\n"
            "Last checked: Just now"
        )
    
    elif query.data in ["enable_all", "errors_only", "disable_all"]:
        settings = {
            "enable_all": "all notifications enabled",
            "errors_only": "only error notifications enabled",
            "disable_all": "all notifications disabled"
        }
        await query.edit_message_text(f"✅ Settings updated: {settings[query.data]}")

async def main():
    """Main function to run the Telegram bot."""
    try:
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            logger.error("TELEGRAM_TOKEN not set in environment variables")
            return
        
        # Create the Application and pass the bot's token
        application = Application.builder().token(token).build()

        # Register command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("getid", getid))
        
        # Register message and callback handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_callback))

        # Start the bot
        logger.info("Telegram bot starting")
        
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for s in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown(application)))
        
        # Start polling mode
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Telegram bot started successfully")
        
        # Keep the bot running until a signal is received
        stop_signal = asyncio.Future()
        await stop_signal
    
    except Exception as e:
        logger.error(f"Telegram bot error: {str(e)}")

async def shutdown(application):
    """Shut down the application gracefully."""
    logger.info("Shutting down...")
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    # Set the stop signal to stop the main loop
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