"""
Telegram Student Verification Bot - Final Version
Optimized for Render.com Web Service
"""

import os
import logging
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update, ParseMode
import random

# ============ CONFIGURATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

# ============ LOGGING SETUP ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ HTTP SERVER FOR RENDER HEALTH CHECKS ============
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP server for Render health checks"""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            response = f"✅ Bot is alive\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Disable access logs to reduce noise"""
        pass

def start_http_server():
    """Start HTTP server in background thread"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        logger.info(f"🌐 HTTP Server started on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ============ UNIVERSITY DATABASE ============
UNIVERSITIES = [
    {"id": 2565, "name": "Pennsylvania State University", "domain": "psu.edu"},
    {"id": 3499, "name": "UCLA", "domain": "ucla.edu"},
    {"id": 3491, "name": "UC Berkeley", "domain": "berkeley.edu"},
    {"id": 3113, "name": "Stanford University", "domain": "stanford.edu"},
    {"id": 2285, "name": "New York University", "domain": "nyu.edu"},
    {"id": 3568, "name": "University of Michigan", "domain": "umich.edu"},
    {"id": 3686, "name": "UT Austin", "domain": "utexas.edu"},
    {"id": 1217, "name": "Georgia Tech", "domain": "gatech.edu"},
    {"id": 602, "name": "Carnegie Mellon", "domain": "cmu.edu"},
    {"id": 3477, "name": "UC San Diego", "domain": "ucsd.edu"},
]

FIRST_NAMES = ["James", "John", "Michael", "David", "Robert", "William", "Richard", "Joseph", "Thomas", "Charles"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

# ============ TELEGRAM BOT HANDLERS ============
def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user = update.effective_user
    
    welcome_text = f"""
👋 *Welcome {user.first_name}!* 🎓

🤖 *Student Verification Bot*
✅ Ready to assist with student status verification

📋 *Available Commands:*
/start - Show this welcome message
/verify - Start verification process  
/mystats - Your verification statistics
/help - Get help and instructions
/status - Check bot status

⚠️ *For educational purposes only*
    """
    
    update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

def verify_command(update: Update, context: CallbackContext):
    """Handle /verify command"""
    
    # Select random university
    university = random.choice(UNIVERSITIES)
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    student_id = f"STU{random.randint(100000, 999999)}"
    
    verification_text = f"""
📋 *Verification Simulation*

👤 *Student Information:*
• Name: {first_name} {last_name}
• Student ID: {student_id}
• University: {university['name']}
• Email: {first_name.lower()}.{last_name.lower()}@{university['domain']}
• Status: Full-time Student

⏱️ *Process:*
✅ Step 1: Information generated
✅ Step 2: University selected
🔄 Step 3: Verification submitted

📅 *Estimated completion:* 24-48 hours
⚠️ *Note:* This is a simulation for educational purposes
    """
    
    update.message.reply_text(verification_text, parse_mode=ParseMode.MARKDOWN)
    
    # Log the verification
    logger.info(f"Verification simulated for {first_name} {last_name} at {university['name']}")

def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    
    help_text = """
📚 *How to Use This Bot*

🔗 *Verification Process:*
1. Use /verify to start
2. Bot will generate student information
3. Simulate verification submission
4. Get estimated completion time

📋 *Available Commands:*
/start - Welcome message
/verify - Start verification
/mystats - Your statistics
/status - Bot status
/help - This message

⚠️ *Important Notes:*
• This bot is for educational purposes
• Simulated data only
• No real verification performed
    """
    
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def status_command(update: Update, context: CallbackContext):
    """Handle /status command"""
    
    status_text = f"""
🤖 *Bot Status Report*

✅ *Status:* Online and Operational
🕒 *Uptime:* {time.strftime('%H:%M:%S')}
🌐 *Server:* Render.com (Web Service)
📊 *Version:* 2.0 Final
🔧 *Environment:* Docker + Python 3.11

📈 *Bot Information:*
• Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}
• Health Check: Active on port {PORT}
• Logging: Enabled

💡 *Tip:* Use /verify to test the bot
    """
    
    update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

def mystats_command(update: Update, context: CallbackContext):
    """Handle /mystats command"""
    user = update.effective_user
    
    stats_text = f"""
📊 *Your Statistics*

👤 *User Info:*
• Name: {user.first_name or 'User'}
• Username: @{user.username or 'N/A'}
• User ID: {user.id}

📅 *Activity:*
• Account created: {datetime.fromtimestamp(user.id >> 32).strftime('%Y-%m-%d') if user.id > 1000000000 else 'N/A'}
• First name: {user.first_name or 'Not set'}
• Language: {user.language_code or 'Not set'}

🎯 *Bot Usage:*
• Commands available: 5
• Universities in database: {len(UNIVERSITIES)}
• Names in database: {len(FIRST_NAMES) + len(LAST_NAMES)}

📝 *Note:* Detailed statistics will be available in future updates
    """
    
    update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

def echo_handler(update: Update, context: CallbackContext):
    """Echo user messages"""
    user_message = update.message.text
    
    if user_message.lower() in ['hi', 'hello', 'hey']:
        update.message.reply_text(f"👋 Hello {update.effective_user.first_name}! Use /help for instructions.")
    elif '?' in user_message:
        update.message.reply_text("🤔 Good question! Use /help for more information.")
    else:
        update.message.reply_text(
            f"📝 You said: *{user_message[:100]}*\n\n"
            f"💡 Try using /verify to start verification or /help for instructions.",
            parse_mode=ParseMode.MARKDOWN
        )

# ============ BOT SETUP ============
def setup_bot():
    """Setup and start the Telegram bot"""
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables!")
        print("=" * 50)
        print("⚠️  IMPORTANT: BOT_TOKEN is not set!")
        print("💡 Go to Render Dashboard → Environment → Add BOT_TOKEN")
        print("=" * 50)
        return None
    
    try:
        # Initialize updater
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Add command handlers
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("verify", verify_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("status", status_command))
        dispatcher.add_handler(CommandHandler("mystats", mystats_command))
        
        # Add message handler
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo_handler))
        
        # Log successful setup
        logger.info("✅ Bot setup completed successfully")
        print("=" * 50)
        print("🤖 Telegram Bot Setup Complete!")
        print(f"🔑 Token: {BOT_TOKEN[:10]}...")
        print(f"🌐 HTTP Port: {PORT}")
        print("=" * 50)
        
        return updater
        
    except Exception as e:
        logger.error(f"❌ Bot setup failed: {e}")
        print(f"❌ Error: {str(e)[:200]}")
        return None

# ============ MAIN FUNCTION ============
def main():
    """Main entry point"""
    
    print("=" * 60)
    print("🚀 Telegram Student Verification Bot")
    print("📦 Optimized for Render.com Web Service")
    print("=" * 60)
    
    # Start HTTP server in background thread (for Render health checks)
    print("🌐 Starting HTTP server for health checks...")
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    print(f"✅ HTTP server started on port {PORT}")
    
    # Setup and start Telegram bot
    print("\n🤖 Setting up Telegram bot...")
    updater = setup_bot()
    
    if updater:
        try:
            print("🚀 Starting bot polling...")
            updater.start_polling()
            print("✅ Bot is now running and ready!")
            print("📱 Find your bot on Telegram and send /start")
            print("\n" + "=" * 60)
            
            # Keep the main thread alive
            updater.idle()
            
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            print(f"❌ Polling error: {str(e)[:200]}")
    else:
        print("❌ Bot setup failed. Check logs for details.")
        
    print("🔄 Bot process ended")

if __name__ == "__main__":
    main()
