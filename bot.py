import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued"""
    user = update.effective_user
    await update.message.reply_text(f"Hello {user.first_name}! Bot is working! ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message"""
    await update.message.reply_text(f"You said: {update.message.text}")

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not found in environment variables!")
        print("Please add BOT_TOKEN to Render environment variables")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Start bot
    print("🤖 Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
