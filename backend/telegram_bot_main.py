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