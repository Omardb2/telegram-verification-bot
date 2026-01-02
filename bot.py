
import os
import logging
from telegram.ext import Updater, CommandHandler

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "PLACEHOLDER_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    """Send welcome message when /start is issued"""
    user = update.effective_user
    update.message.reply_text(f"✅ Bot is working! Hello {user.first_name}!")

def help_command(update, context):
    """Send help message"""
    update.message.reply_text("Send /start to begin")

def main():
    """Start the bot"""
    if BOT_TOKEN == "PLACEHOLDER_TOKEN":
        print("⚠️ WARNING: Using placeholder token")
        print("   Add real BOT_TOKEN in Render environment variables")
    
    try:
        # Create Updater with older API style
        updater = Updater(token=BOT_TOKEN, use_context=True)
        
        # Get dispatcher
        dp = updater.dispatcher
        
        # Add handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        
        # Start bot
        print("🤖 Bot starting with Python 3.11...")
        updater.start_polling()
        print("✅ Bot is running successfully!")
        
        # Keep running
        updater.idle()
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")
        print("💡 Make sure BOT_TOKEN is set correctly")

if __name__ == "__main__":
    main()
