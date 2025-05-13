from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
import os

# Replace 'YOUR_BOT_TOKEN' with the token from BotFather
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /getid command."""
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass the bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Register the /getid command handler
    application.add_handler(CommandHandler("getid", getid))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()