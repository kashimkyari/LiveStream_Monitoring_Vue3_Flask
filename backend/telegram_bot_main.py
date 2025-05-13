import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging to match Flask app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /getid command."""
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")

async def main():
    """Main function to run the Telegram bot."""
    try:
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            logger.error("TELEGRAM_TOKEN not set in environment variables")
            return
        
        # Create the Application and pass the bot's token
        application = Application.builder().token(token).build()

        # Register the /getid command handler
        application.add_handler(CommandHandler("getid", getid))

        # Start polling
        logger.info("Telegram bot starting")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Run the bot until the user presses Ctrl-C
        logger.info("Telegram bot started successfully")
        
        # Keep the bot running
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        
    except Exception as e:
        logger.error(f"Telegram bot error: {str(e)}")

def run_bot():
    """Run the bot in the event loop."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Telegram bot stopped by user")
    except Exception as e:
        logger.error(f"Telegram bot error in event loop: {str(e)}")

if __name__ == "__main__":
    run_bot()