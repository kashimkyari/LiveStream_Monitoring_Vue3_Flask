import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging to match main.py
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
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Telegram bot started")
    except Exception as e:
        logger.error(f"Telegram bot error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())