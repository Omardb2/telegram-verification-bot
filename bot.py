import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "PLACEHOLDER_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued"""
    user = update.effective_user
    await update.message.reply_text(f"🚀 Hello {user.first_name}! Bot is working! ✅")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await update.message.reply_text("Help command - Bot is functional!")

def main():
    """Start the bot"""
    if not BOT_TOKEN or BOT_TOKEN == "PLACEHOLDER_TOKEN":
        print("⚠️ WARNING: Using placeholder token. Bot will not connect to Telegram.")
        print("   Please add your real BOT_TOKEN in Render environment variables")
    
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Simple echo handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
            lambda update, context: update.message.reply_text(f"Echo: {update.message.text}")))
        
        # Start bot
        print("🤖 Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        print("⚠️ Check your BOT_TOKEN and internet connection")

if __name__ == "__main__":
    main()
