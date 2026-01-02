import os
import logging
from telegram.ext import Updater, CommandHandler

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    """Send welcome message when /start is issued"""
    user = update.effective_user
    update.message.reply_text(
        f"🎓 Welcome {user.first_name}!\n\n"
        f"🤖 Student Verification Bot\n"
        f"✅ Ready to help with verification\n\n"
        f"Use /help for instructions"
    )

def help_command(update, context):
    """Send help message"""
    help_text = """
📚 *How to use this bot:*

1. Get your verification link
2. Send it to this bot
3. Wait for processing
4. Receive confirmation

🔗 *Commands:*
/start - Welcome message
/help - This help message
/status - Check bot status

⚠️ *Note:* For educational purposes only
    """
    update.message.reply_text(help_text)

def status(update, context):
    """Check bot status"""
    update.message.reply_text("✅ Bot is online and operational!")

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not set in environment variables!")
        print("Please set BOT_TOKEN in Render environment variables")
        return
    
    try:
        print("=" * 50)
        print("🤖 Starting Telegram Bot...")
        print(f"✅ Token: {BOT_TOKEN[:10]}...")
        print("=" * 50)
        
        # Create Updater
        updater = Updater(token=BOT_TOKEN, use_context=True)
        
        # Get dispatcher
        dp = updater.dispatcher
        
        # Add handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("status", status))
        
        # Start bot
        print("🚀 Bot starting polling...")
        updater.start_polling()
        
        print("✅ Bot is running successfully!")
        print("📱 Find your bot on Telegram")
        
        # Keep running
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        print(f"Error details: {str(e)[:200]}")

if __name__ == "__main__":
    main()
