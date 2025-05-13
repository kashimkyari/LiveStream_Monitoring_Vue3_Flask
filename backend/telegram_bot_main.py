import os
import asyncio
import logging
import signal
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = 'https://monitor-backend.jetcamstudio.com:5000'
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# User sessions
user_sessions = {}

# Conversation states
USERNAME, PASSWORD, AI_CHAT = range(3)

# Define keyboard layouts
def get_main_keyboard():
    keyboard = [
        ["📺 My Streams", "🔔 Notifications"],
        ["🤖 AI Assistant", "📊 Dashboard"],
        ["ℹ️ Help", "🆔 Get My ID"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# API Helper Function
async def api_request(method, endpoint, data=None, token=None):
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    try:
        response = requests.request(method, url, headers=headers, json=data, timeout=10)
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()
        else:
            return {'error': f"API Error ({response.status_code}): {response.text}"}
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return {'error': f"Connection error: {str(e)}"}

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if user_id in user_sessions and 'token' in user_sessions[user_id]:
        await update.message.reply_text(
            f"👋 Welcome back, {user_name}! You're already logged in.",
            reply_markup=get_main_keyboard()
        )
    else:
        welcome_message = (
            f"👋 Welcome, {user_name}! I'm your LiveStream Monitoring Bot.\n\n"
            "Please login to access personalized features."
        )
        await update.message.reply_text(
            welcome_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔑 Login", callback_data="login")]])
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in user_sessions or 'token' not in user_sessions[user_id]:
        await update.message.reply_text("Please login first using /login")
        return
    help_text = (
        "🔹 *LiveStream Monitoring Bot Help* 🔹\n\n"
        "**Commands:**\n"
        "- /start - Start the bot and login\n"
        "- /help - Show this help message\n"
        "- /getid - Get your chat ID\n"
        "- /login - Login to your account\n"
        "- /logout - Logout from your account\n\n"
        "**Features:**\n"
        "- 📺 *My Streams* - View your assigned streams\n"
        "- 🔔 *Notifications* - View your notifications\n"
        "- 🤖 *AI Assistant* - Get AI-powered help\n"
        "- 📊 *Dashboard* - Open the monitoring dashboard\n"
        "- ℹ️ *Help* - Show this help message\n"
        "- 🆔 *Get My ID* - Get your chat ID"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_id = update.effective_user.id
    message = f"Your chat ID is: `{chat_id}`\nUse this ID to set up notifications."
    if user_id in user_sessions and 'token' in user_sessions[user_id]:
        token = user_sessions[user_id]['token']
        response = await api_request('post', 'user/telegram', data={'telegram_chat_id': str(chat_id), 'receive_updates': True}, token=token)
        if 'error' not in response:
            message += "\n✅ Chat ID linked to your account!"
    await update.message.reply_text(message, parse_mode="Markdown")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_sessions:
        token = user_sessions[user_id].get('token')
        if token:
            await api_request('post', 'logout', token=token)
        del user_sessions[user_id]
    await update.message.reply_text("You have been logged out.")

# Login Conversation
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter your username:")
    return USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_sessions[user_id] = {'username': update.message.text}
    await update.message.reply_text("Please enter your password:")
    return PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    password = update.message.text
    username = user_sessions[user_id]['username']
    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Error deleting password message: {e}")
    response = await api_request('post', 'login', data={'username': username, 'password': password})
    if 'token' in response:
        user_sessions[user_id]['token'] = response['token']
        await update.message.reply_text("Login successful!", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Login failed. Try again with /login")
        return ConversationHandler.END

# AI Assistant Conversation
system_prompt = """
You are an AI assistant for a livestream monitoring system. You can help users with:
- Understanding how to use the monitoring features
- Setting up notifications
- Troubleshooting stream issues
- Suggesting automations (e.g., notification triggers)
Be concise and helpful.
"""

async def ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("You are now talking to the AI Assistant. Type 'exit' to end.")
    return AI_CHAT

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    if user_message.lower() == 'exit':
        await update.message.reply_text("Exiting AI Assistant.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    response = await get_ai_response(user_message)
    await update.message.reply_text(response)
    return AI_CHAT

async def get_ai_response(message):
    if not DEEPSEEK_API_KEY:
        return "AI Assistant unavailable: API key not set."
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-coder",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 150
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return "Error: Could not get AI response."
    except Exception as e:
        logger.error(f"AI API error: {e}")
        return "Error communicating with AI."

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in user_sessions or 'token' not in user_sessions[user_id]:
        await update.message.reply_text("Please login first using /login")
        return
    text = update.message.text
    token = user_sessions[user_id]['token']

    if text == "📺 My Streams":
        response = await api_request('get', 'agent/dashboard', token=token)
        if 'error' in response:
            await update.message.reply_text(f"Error: {response['error']}")
        else:
            streams = response.get('assignments', [])
            if not streams:
                await update.message.reply_text("No assigned streams.")
            else:
                message = f"Your Streams ({response.get('ongoing_streams', 0)} ongoing):\n"
                for stream in streams:
                    stream_id = stream['stream_id']
                    status = "🟢" if stream['stream'].get('active') else "⚫"
                    message += f"{status} Stream #{stream_id}: {stream['stream']['stream_url']}\n"
                await update.message.reply_text(message)

    elif text == "🔔 Notifications":
        response = await api_request('get', 'agent/notifications', token=token)
        if 'error' in response:
            await update.message.reply_text(f"Error: {response['error']}")
        else:
            notifications = response.get('notifications', [])
            if not notifications:
                await update.message.reply_text("No notifications.")
            else:
                unread = sum(1 for n in notifications if not n['read'])
                message = f"Notifications ({unread} unread):\n"
                for n in notifications[:5]:
                    status = "✓" if n['read'] else "🔴"
                    message += f"{status} #{n['id']}: {n['message']}\n"
                buttons = [[InlineKeyboardButton("📖 Mark All Read", callback_data="read_all_notifications")]]
                await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "🤖 AI Assistant":
        await ai_start(update, context)

    elif text == "📊 Dashboard":
        dashboard_url = "https://monitor.jetcamstudio.com/"
        await update.message.reply_text(
            "Open your dashboard:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 Dashboard", url=dashboard_url)]])
        )

    elif text == "ℹ️ Help":
        await help_command(update, context)

    elif text == "🆔 Get My ID":
        await getid(update, context)

    else:
        await update.message.reply_text("Use the menu to interact.", reply_markup=get_main_keyboard())

# Callback Handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "login":
        await query.edit_message_text("Use /login to start the login process.")
        return

    if user_id not in user_sessions or 'token' not in user_sessions[user_id]:
        await query.edit_message_text("Please login first with /login")
        return

    token = user_sessions[user_id]['token']

    if query.data == "read_all_notifications":
        response = await api_request('put', 'agent/notifications/read-all', token=token)
        if 'error' in response:
            await query.edit_message_text(f"Error: {response['error']}")
        else:
            await query.edit_message_text(f"✅ Marked {response.get('count', 0)} notifications as read.")

# Main Function
async def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logger.error("TELEGRAM_TOKEN not set")
        return
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("getid", getid))
    application.add_handler(CommandHandler("logout", logout))

    login_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        },
        fallbacks=[],
    )
    application.add_handler(login_handler)

    ai_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('🤖 AI Assistant'), ai_start)],
        states={
            AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat)],
        },
        fallbacks=[],
    )
    application.add_handler(ai_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot started successfully")
    stop_signal = asyncio.Future()
    await stop_signal

if __name__ == "__main__":
    asyncio.run(main())