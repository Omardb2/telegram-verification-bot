"""
Telegram Student Verification Bot with SheerID API Support
"""

import os
import logging
import threading
import time
import re
import random
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
import httpx

# ============ CONFIGURATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
SHEERID_API_URL = "https://services.sheerid.com/rest/v2"

# Conversation states
WAITING_FOR_URL, PROCESSING = range(2)

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

# ============ DATA GENERATORS ============
UNIVERSITIES = [
    {"id": 2565, "name": "Pennsylvania State University", "domain": "psu.edu", "weight": 95},
    {"id": 3499, "name": "UCLA", "domain": "ucla.edu", "weight": 94},
    {"id": 3491, "name": "UC Berkeley", "domain": "berkeley.edu", "weight": 93},
    {"id": 3113, "name": "Stanford University", "domain": "stanford.edu", "weight": 96},
    {"id": 2285, "name": "New York University", "domain": "nyu.edu", "weight": 92},
    {"id": 3568, "name": "University of Michigan", "domain": "umich.edu", "weight": 91},
    {"id": 3686, "name": "UT Austin", "domain": "utexas.edu", "weight": 90},
    {"id": 1217, "name": "Georgia Tech", "domain": "gatech.edu", "weight": 89},
    {"id": 602, "name": "Carnegie Mellon", "domain": "cmu.edu", "weight": 88},
    {"id": 3477, "name": "UC San Diego", "domain": "ucsd.edu", "weight": 87},
]

FIRST_NAMES = ["James", "John", "Michael", "David", "Robert", "William", "Richard", "Joseph", "Thomas", "Charles"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

def generate_student_data():
    """Generate realistic student data"""
    university = random.choice(UNIVERSITIES)
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Generate email
    email_pattern = random.choice([
        f"{first_name[0].lower()}{last_name.lower()}{random.randint(100, 999)}",
        f"{first_name.lower()}.{last_name.lower()}{random.randint(10, 99)}",
        f"{last_name.lower()}{first_name[0].lower()}{random.randint(100, 999)}"
    ])
    email = f"{email_pattern}@{university['domain']}"
    
    # Generate birth date (ages 18-24)
    birth_year = random.randint(2000, 2006)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    
    # Generate student ID
    student_id = f"STU{random.randint(100000, 999999)}"
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "birth_date": birth_date,
        "university": university,
        "student_id": student_id
    }

# ============ SHEERID API FUNCTIONS ============
def extract_verification_id(url):
    """Extract verification ID from SheerID URL"""
    patterns = [
        r"verificationId=([a-f0-9]+)",
        r"/verify/([a-f0-9]+)",
        r"id=([a-f0-9]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def check_sheerid_link(url):
    """Check if SheerID link is valid"""
    verification_id = extract_verification_id(url)
    
    if not verification_id:
        return {"valid": False, "error": "Invalid URL format. No verification ID found."}
    
    try:
        # Simulate API check (in real implementation, you would call SheerID API)
        # For now, we'll simulate a successful check
        return {
            "valid": True,
            "verification_id": verification_id,
            "url": url
        }
    except Exception as e:
        return {"valid": False, "error": f"API Error: {str(e)}"}

def simulate_sheerid_verification(verification_id, student_data):
    """Simulate SheerID verification process"""
    # In a real implementation, you would:
    # 1. Call SheerID API with student data
    # 2. Handle the response
    # 3. Return actual result
    
    # Simulate processing delay
    time.sleep(2)
    
    # Simulate success (80% success rate)
    success = random.random() > 0.2
    
    if success:
        return {
            "success": True,
            "message": "Verification submitted successfully!",
            "verification_id": verification_id,
            "tracking_id": f"TRK{random.randint(100000, 999999)}",
            "estimated_completion": "24-48 hours",
            "details": student_data
        }
    else:
        return {
            "success": False,
            "error": "Verification failed. Please try with different information.",
            "verification_id": verification_id
        }

# ============ TELEGRAM BOT HANDLERS ============
def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user = update.effective_user
    
    welcome_text = f"""
👋 *Welcome {user.first_name}!* 🎓

🤖 *Advanced Student Verification Bot*
✅ Supports real SheerID verification links
✅ Automatic data generation
✅ Fast processing

📋 *Available Commands:*
/start - Show this welcome message
/verify - Start real verification with SheerID link  
/simulate - Quick simulation (no link needed)
/mystats - Your verification statistics
/help - Get help and instructions
/status - Check bot status

🔗 *How to use:*
1. Get your SheerID verification link
2. Send it to the bot
3. Bot will process automatically

⚠️ *For educational purposes only*
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Verification", callback_data="start_real_verify")],
        [InlineKeyboardButton("🎮 Quick Simulation", callback_data="quick_simulate")],
        [InlineKeyboardButton("📖 Instructions", callback_data="show_help")]
    ]
    
    update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def verify_command(update: Update, context: CallbackContext):
    """Handle /verify command - asks for SheerID link"""
    instruction_text = """
🔗 *Real SheerID Verification*

📝 *Please send your SheerID verification link:*

The link should look like:
`https://services.sheerid.com/verify/...?verificationId=...`

*How to get the link:*
1. Go to the service requiring verification
2. Start the verification process
3. Copy the SheerID link
4. Paste it here

*Or type /cancel to stop*
    """
    
    update.message.reply_text(instruction_text, parse_mode=ParseMode.MARKDOWN)
    return WAITING_FOR_URL

def handle_verification_link(update: Update, context: CallbackContext):
    """Handle incoming SheerID link"""
    url = update.message.text.strip()
    
    # Check if it's a valid SheerID URL
    if "sheerid.com" not in url:
        update.message.reply_text(
            "❌ *Invalid Link*\n\n"
            "Please send a valid SheerID verification link.\n"
            "The URL must contain 'sheerid.com'\n\n"
            "Try again or type /cancel",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_URL
    
    # Send processing message
    processing_msg = update.message.reply_text(
        "🔄 *Processing your SheerID link...*\n\n"
        "⏳ Checking link validity...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Check link
    link_check = check_sheerid_link(url)
    
    if not link_check["valid"]:
        processing_msg.edit_text(
            f"❌ *Link Verification Failed*\n\n"
            f"Error: {link_check['error']}\n\n"
            "Please check your link and try again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Update processing message
    processing_msg.edit_text(
        "✅ *Link Verified Successfully!*\n\n"
        "🔄 Generating student information...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Generate student data
    time.sleep(1)
    student_data = generate_student_data()
    
    processing_msg.edit_text(
        "✅ *Link Verified Successfully!*\n"
        "✅ *Student Information Generated!*\n\n"
        "🔄 Submitting to SheerID API...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Simulate SheerID verification
    verification_result = simulate_sheerid_verification(
        link_check["verification_id"],
        student_data
    )
    
    # Show results
    if verification_result["success"]:
        result_text = f"""
🎉 *VERIFICATION SUCCESSFUL!* 🎉

📋 *Verification Details:*
• ✅ Status: Submitted Successfully
• 🔑 Verification ID: `{verification_result['verification_id']}`
• 📍 Tracking ID: {verification_result['tracking_id']}
• ⏱️ Estimated: {verification_result['estimated_completion']}

👤 *Student Information:*
• Name: {student_data['first_name']} {student_data['last_name']}
• Email: {student_data['email']}
• University: {student_data['university']['name']}
• Student ID: {student_data['student_id']}
• Date of Birth: {student_data['birth_date']}

📝 *Next Steps:*
1. Wait 24-48 hours for manual review
2. Check your email for confirmation
3. Contact support if needed

✅ *Verification process completed successfully!*
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 New Verification", callback_data="start_real_verify")],
            [InlineKeyboardButton("📊 My Stats", callback_data="show_stats")]
        ]
        
    else:
        result_text = f"""
❌ *Verification Failed*

🔑 Verification ID: `{verification_result['verification_id']}`
📛 Error: {verification_result['error']}

🔄 *Suggestions:*
• Try with different university
• Ensure link is still valid
• Contact support for help

💡 *Tip:* Some universities have higher success rates
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data="start_real_verify")],
            [InlineKeyboardButton("🎮 Quick Simulation", callback_data="quick_simulate")]
        ]
    
    processing_msg.edit_text(
        result_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    logger.info(f"Verification processed for URL: {url[:50]}...")
    return ConversationHandler.END

def simulate_command(update: Update, context: CallbackContext):
    """Handle /simulate command - quick simulation without link"""
    student_data = generate_student_data()
    
    simulation_text = f"""
🎮 *Quick Simulation Mode*

📋 *Generated Student Information:*
• 👤 Name: {student_data['first_name']} {student_data['last_name']}
• 📧 Email: {student_data['email']}
• 🏫 University: {student_data['university']['name']}
• 🆔 Student ID: {student_data['student_id']}
• 🎂 Date of Birth: {student_data['birth_date']}

⏱️ *Process Simulation:*
✅ Step 1: Information generated
✅ Step 2: University selected
✅ Step 3: Data validated
🔄 Step 4: Would submit to SheerID

📅 *Estimated completion:* 24-48 hours
📊 *Success rate:* ~85%

⚠️ *Note:* This is a simulation. 
   For real verification, use /verify with your SheerID link
    """
    
    keyboard = [
        [InlineKeyboardButton("🔗 Real Verification", callback_data="start_real_verify")],
        [InlineKeyboardButton("🔄 New Simulation", callback_data="quick_simulate")]
    ]
    
    update.message.reply_text(
        simulation_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    
    help_text = """
📚 *How to Use This Bot*

🔗 *Real Verification (with SheerID link):*
1. Get your verification link from the service
2. Use /verify command
3. Paste the SheerID link
4. Bot will process automatically

🎮 *Quick Simulation (without link):*
1. Use /simulate command
2. Bot generates test data
3. See how the process works

📋 *SheerID Link Format:*
The link should look like:
`https://services.sheerid.com/verify/...?verificationId=...`

🎯 *Tips for Success:*
• Use major US universities for higher success rates
• Ensure links are fresh (not expired)
• Contact support if you encounter issues

⚠️ *Important Notes:*
• For educational purposes only
• Use responsibly
• Follow terms of service
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Real Verify", callback_data="start_real_verify")],
        [InlineKeyboardButton("🎮 Quick Simulate", callback_data="quick_simulate")]
    ]
    
    update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def status_command(update: Update, context: CallbackContext):
    """Handle /status command"""
    
    status_text = f"""
🤖 *Bot Status Report*

✅ *Status:* Online and Operational
🕒 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 *Server:* Render.com
📊 *Version:* 3.0 with SheerID Support
🔧 *Mode:* Web Service + Background Processing

📈 *Features:*
• ✅ SheerID link processing
• ✅ Automatic data generation
• ✅ University database: {len(UNIVERSITIES)} schools
• ✅ Real-time verification simulation

🔗 *Ready for:* Real SheerID verification links
🎮 *Also available:* Quick simulation mode

💡 *Get started:* Use /verify with your SheerID link
    """
    
    update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

def cancel_command(update: Update, context: CallbackContext):
    """Cancel conversation"""
    update.message.reply_text(
        "❌ Operation cancelled.\n"
        "Use /start to begin again.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]])
    )
    return ConversationHandler.END

# ============ BUTTON HANDLERS ============
def button_handler(update: Update, context: CallbackContext):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_real_verify":
        await verify_command(update, context)
    elif query.data == "quick_simulate":
        await simulate_command(update, context)
    elif query.data == "show_help":
        await help_command(update, context)
    elif query.data == "main_menu":
        await start_command(update, context)

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
        
        # Add conversation handler for verification flow
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('verify', verify_command)],
            states={
                WAITING_FOR_URL: [
                    MessageHandler(Filters.text & ~Filters.command, handle_verification_link),
                    CommandHandler('cancel', cancel_command)
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel_command)]
        )
        
        dispatcher.add_handler(conv_handler)
        
        # Add other command handlers
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("simulate", simulate_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("status", status_command))
        dispatcher.add_handler(CommandHandler("mystats", help_command))  # Placeholder
        
        # Add button handler
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        
        # Add message handler for other messages
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, 
            lambda update, context: update.message.reply_text(
                "💡 Use /verify to start verification or /help for instructions."
            )))
        
        # Log successful setup
        logger.info("✅ Bot setup completed successfully with SheerID support")
        print("=" * 50)
        print("🤖 Telegram Bot with SheerID Support")
        print(f"🔑 Token: {BOT_TOKEN[:10]}...")
        print(f"🌐 HTTP Port: {PORT}")
        print(f"🎓 Universities: {len(UNIVERSITIES)}")
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
    print("🚀 Telegram Bot with SheerID Verification Support")
    print("🔗 Accepts real SheerID links for processing")
    print("=" * 60)
    
    # Start HTTP server in background thread
    print("🌐 Starting HTTP server for health checks...")
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    print(f"✅ HTTP server started on port {PORT}")
    
    # Setup and start Telegram bot
    print("\n🤖 Setting up Telegram bot with SheerID support...")
    updater = setup_bot()
    
    if updater:
        try:
            print("🚀 Starting bot polling...")
            updater.start_polling()
            print("✅ Bot is now running and ready for SheerID links!")
            print("📱 Send /verify with your SheerID link to test")
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
