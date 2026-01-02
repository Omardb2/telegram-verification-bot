"""
Telegram Student Verification Bot - Real SheerID API
Complete automation with document generation and upload
"""

import os
import logging
import threading
import time
import re
import random
import hashlib
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from pathlib import Path

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
import httpx
from PIL import Image, ImageDraw, ImageFont

# ============ CONFIGURATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
SHEERID_API_URL = "https://services.sheerid.com/rest/v2"
PROGRAM_ID = "67c8c14f5f17a83b745e3f82"

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

# ============ DOCUMENT GENERATION ============
def generate_student_id_image(first_name, last_name, university_name, student_id, birth_date):
    """Create professional student ID card"""
    width, height = 650, 400
    
    # Create image with white background
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Try to load fonts
    try:
        # Try system fonts
        title_font = ImageFont.truetype("arialbd.ttf", 28) if os.path.exists("arialbd.ttf") else ImageFont.load_default()
        header_font = ImageFont.truetype("arial.ttf", 22) if os.path.exists("arial.ttf") else ImageFont.load_default()
        text_font = ImageFont.truetype("arial.ttf", 18) if os.path.exists("arial.ttf") else ImageFont.load_default()
        small_font = ImageFont.truetype("arial.ttf", 14) if os.path.exists("arial.ttf") else ImageFont.load_default()
    except:
        title_font = header_font = text_font = small_font = ImageFont.load_default()
    
    # University colors
    uni_colors = {
        "primary": (0, 40, 85),
        "secondary": (200, 16, 46),
        "accent": (248, 249, 250)
    }
    
    # Header section
    draw.rectangle([(0, 0), (width, 70)], fill=uni_colors["primary"])
    draw.text(
        (width // 2, 35),
        "STUDENT IDENTIFICATION CARD",
        fill=(255, 255, 255),
        font=title_font,
        anchor="mm"
    )
    
    # University name
    draw.text(
        (width // 2, 100),
        university_name[:40],
        fill=uni_colors["primary"],
        font=header_font,
        anchor="mm"
    )
    
    # Photo placeholder
    photo_x1, photo_y1 = 40, 140
    photo_x2, photo_y2 = 180, 320
    
    draw.rectangle(
        [(photo_x1, photo_y1), (photo_x2, photo_y2)],
        outline=(200, 200, 200),
        width=3
    )
    
    draw.text(
        ((photo_x1 + photo_x2) // 2, (photo_y1 + photo_y2) // 2),
        "STUDENT\nPHOTO",
        fill=(180, 180, 180),
        font=text_font,
        anchor="mm",
        align="center"
    )
    
    # Student information
    info_start_x = 220
    info_y = 150
    
    info_lines = [
        f"NAME: {first_name} {last_name}",
        f"STUDENT ID: {student_id}",
        f"STATUS: FULL-TIME STUDENT",
        f"MAJOR: COMPUTER SCIENCE",
        f"DATE OF BIRTH: {birth_date}",
        f"VALID: {datetime.now().year}-{datetime.now().year + 1}"
    ]
    
    for i, line in enumerate(info_lines):
        draw.text(
            (info_start_x, info_y + (i * 35)),
            line,
            fill=(30, 30, 30),
            font=text_font
        )
    
    # Barcode simulation
    bar_y = 340
    for i in range(25):
        bar_x = 40 + (i * 25)
        bar_height = random.randint(40, 80)
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + 15, bar_y + bar_height)],
            fill=(0, 0, 0)
        )
    
    # Footer
    draw.rectangle([(0, height - 50), (width, height)], fill=uni_colors["primary"])
    draw.text(
        (width // 2, height - 25),
        "OFFICIAL UNIVERSITY DOCUMENT • VALID WITH PHOTO ID",
        fill=(255, 255, 255),
        font=small_font,
        anchor="mm"
    )
    
    # Convert to bytes
    img_io = BytesIO()
    image.save(img_io, 'PNG', quality=95)
    img_io.seek(0)
    return img_io

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

def verify_sheerid_link(verification_id):
    """Verify if SheerID link is valid"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{SHEERID_API_URL}/verification/{verification_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                current_step = data.get("currentStep", "")
                
                if current_step in ["collectStudentPersonalInfo", "sso"]:
                    return {"valid": True, "step": current_step}
                elif current_step == "success":
                    return {"valid": False, "error": "Already verified"}
                else:
                    return {"valid": False, "error": f"Invalid step: {current_step}"}
            else:
                return {"valid": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"valid": False, "error": f"Connection error: {str(e)}"}

def submit_to_sheerid(verification_id, student_data, image_io):
    """Submit complete verification to SheerID"""
    try:
        with httpx.Client(timeout=30.0) as client:
            # Generate fingerprint
            fingerprint = hashlib.md5(
                f"{time.time()}{random.random()}".encode()
            ).hexdigest()
            
            # Step 1: Submit student information
            student_payload = {
                "firstName": student_data["first_name"],
                "lastName": student_data["last_name"],
                "birthDate": student_data["birth_date"],
                "email": student_data["email"],
                "phoneNumber": "",
                "organization": {
                    "id": student_data["university"]["id"],
                    "idExtended": str(student_data["university"]["id"]),
                    "name": student_data["university"]["name"]
                },
                "deviceFingerprintHash": fingerprint,
                "locale": "en-US",
                "metadata": {
                    "marketConsentValue": False,
                    "verificationId": verification_id,
                    "refererUrl": f"https://services.sheerid.com/verify/{PROGRAM_ID}/?verificationId={verification_id}",
                    "flags": json.dumps({
                        "collect-info-step-email-first": "default",
                        "doc-upload-considerations": "default",
                        "font-size": "default"
                    }),
                    "submissionOptIn": "I agree to the terms and conditions"
                }
            }
            
            logger.info(f"Submitting student info to SheerID: {student_data['first_name']} {student_data['last_name']}")
            
            response = client.post(
                f"{SHEERID_API_URL}/verification/{verification_id}/step/collectStudentPersonalInfo",
                json=student_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Student info submission failed: HTTP {response.status_code}"
                }
            
            # Step 2: Get upload URL
            file_size = image_io.getbuffer().nbytes
            upload_payload = {
                "files": [{
                    "fileName": "student_id_card.png",
                    "mimeType": "image/png",
                    "fileSize": file_size
                }]
            }
            
            response = client.post(
                f"{SHEERID_API_URL}/verification/{verification_id}/step/docUpload",
                json=upload_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Upload URL request failed: HTTP {response.status_code}"
                }
            
            upload_data = response.json()
            
            if not upload_data.get("documents"):
                return {
                    "success": False,
                    "error": "No upload URL received"
                }
            
            upload_url = upload_data["documents"][0].get("uploadUrl")
            if not upload_url:
                return {
                    "success": False,
                    "error": "Invalid upload URL"
                }
            
            # Step 3: Upload document
            image_io.seek(0)
            response = client.put(
                upload_url,
                content=image_io.read(),
                headers={"Content-Type": "image/png"}
            )
            
            if response.status_code not in [200, 204]:
                return {
                    "success": False,
                    "error": f"Document upload failed: HTTP {response.status_code}"
                }
            
            # Step 4: Complete upload
            response = client.post(
                f"{SHEERID_API_URL}/verification/{verification_id}/step/completeDocUpload"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Upload completion failed: HTTP {response.status_code}"
                }
            
            # Get final status
            final_response = client.get(
                f"{SHEERID_API_URL}/verification/{verification_id}"
            )
            
            if final_response.status_code == 200:
                final_data = final_response.json()
                return {
                    "success": True,
                    "message": "Verification submitted successfully!",
                    "verification_id": verification_id,
                    "current_step": final_data.get("currentStep", "pending"),
                    "details": student_data
                }
            else:
                return {
                    "success": True,
                    "message": "Verification submitted! (Status check failed)",
                    "verification_id": verification_id,
                    "details": student_data
                }
                
    except Exception as e:
        logger.error(f"SheerID submission error: {e}")
        return {
            "success": False,
            "error": f"API Error: {str(e)[:100]}"
        }

# ============ TELEGRAM BOT HANDLERS ============
def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user = update.effective_user
    
    welcome_text = f"""
👋 *Welcome {user.first_name}!* 🎓

🤖 *Advanced Student Verification Bot*
✅ Real SheerID API integration
✅ Automatic document generation
✅ Complete verification automation

📋 *Available Commands:*
/start - Show this welcome message
/verify - Start real SheerID verification  
/simulate - Quick simulation (no link needed)
/help - Get help and instructions
/status - Check bot status

🔗 *How to use:*
1. Get your SheerID verification link
2. Send it to the bot
3. Bot will automatically:
   • Generate student information
   • Create student ID card
   • Submit to SheerID
   • Upload document

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
1. Go to the service requiring verification (Google One, Spotify, etc.)
2. Start the student verification process
3. Copy the SheerID verification link
4. Paste it here

*The bot will automatically:*
✅ Extract verification ID
✅ Generate student information
✅ Create student ID card
✅ Submit to SheerID API
✅ Upload document

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
    
    # Extract verification ID
    verification_id = extract_verification_id(url)
    if not verification_id:
        update.message.reply_text(
            "❌ *Invalid Link Format*\n\n"
            "Could not extract verification ID from the link.\n"
            "Make sure it contains 'verificationId=' parameter.\n\n"
            "Try again or type /cancel",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_URL
    
    # Send processing message
    processing_msg = update.message.reply_text(
        "🔄 *Processing your SheerID link...*\n\n"
        "⏳ Step 1/5: Extracting verification ID...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Verify link
    time.sleep(1)
    processing_msg.edit_text(
        "🔄 *Processing your SheerID link...*\n\n"
        "✅ Step 1/5: Verification ID extracted\n"
        "⏳ Step 2/5: Verifying link with SheerID...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    link_check = verify_sheerid_link(verification_id)
    
    if not link_check["valid"]:
        processing_msg.edit_text(
            f"❌ *Link Verification Failed*\n\n"
            f"Error: {link_check['error']}\n\n"
            "Please check your link and try again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    
    # Generate student data
    time.sleep(1)
    processing_msg.edit_text(
        "🔄 *Processing your SheerID link...*\n\n"
        "✅ Step 1/5: Verification ID extracted\n"
        "✅ Step 2/5: Link verified with SheerID\n"
        "⏳ Step 3/5: Generating student information...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    student_data = generate_student_data()
    
    # Generate student ID image
    time.sleep(1)
    processing_msg.edit_text(
        "🔄 *Processing your SheerID link...*\n\n"
        "✅ Step 1/5: Verification ID extracted\n"
        "✅ Step 2/5: Link verified with SheerID\n"
        "✅ Step 3/5: Student information generated\n"
        "⏳ Step 4/5: Creating student ID card...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    image_io = generate_student_id_image(
        student_data["first_name"],
        student_data["last_name"],
        student_data["university"]["name"],
        student_data["student_id"],
        student_data["birth_date"]
    )
    
    # Submit to SheerID
    time.sleep(1)
    processing_msg.edit_text(
        "🔄 *Processing your SheerID link...*\n\n"
        "✅ Step 1/5: Verification ID extracted\n"
        "✅ Step 2/5: Link verified with SheerID\n"
        "✅ Step 3/5: Student information generated\n"
        "✅ Step 4/5: Student ID card created\n"
        "⏳ Step 5/5: Submitting to SheerID API...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Submit to SheerID API
    result = submit_to_sheerid(verification_id, student_data, image_io)
    
    # Show results
    if result["success"]:
        result_text = f"""
🎉 *VERIFICATION SUBMITTED SUCCESSFULLY!* 🎉

📋 *SheerID Details:*
• ✅ Status: Submitted Successfully
• 🔑 Verification ID: `{verification_id}`
• 📍 Current Step: {result.get('current_step', 'pending_review')}
• 📄 Document: Uploaded successfully

👤 *Student Information:*
• Name: {student_data['first_name']} {student_data['last_name']}
• Email: {student_data['email']}
• University: {student_data['university']['name']}
• Student ID: {student_data['student_id']}
• Date of Birth: {student_data['birth_date']}

🖼️ *Document Generated:*
• Type: Student ID Card
• Format: PNG
• Status: Uploaded to SheerID

📝 *Next Steps:*
1. Wait 24-48 hours for manual review
2. Check your email for confirmation
3. Contact support if needed

✅ *Complete automation process finished!*
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 New Verification", callback_data="start_real_verify")],
            [InlineKeyboardButton("📊 Statistics", callback_data="show_stats")]
        ]
        
    else:
        result_text = f"""
❌ *Verification Failed*

🔑 Verification ID: `{verification_id}`
📛 Error: {result['error']}

👤 *Generated Information (not submitted):*
• Name: {student_data['first_name']} {student_data['last_name']}
• University: {student_data['university']['name']}
• Email: {student_data['email']}

🔄 *Possible Solutions:*
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
    
    logger.info(f"Verification processed for ID: {verification_id}")
    return ConversationHandler.END

def simulate_command(update: Update, context: CallbackContext):
    """Handle /simulate command - quick simulation without link"""
    student_data = generate_student_data()
    
    # Generate image for demonstration
    image_io = generate_student_id_image(
        student_data["first_name"],
        student_data["last_name"],
        student_data["university"]["name"],
        student_data["student_id"],
        student_data["birth_date"]
    )
    file_size = image_io.getbuffer().nbytes
    
    simulation_text = f"""
🎮 *Quick Simulation Mode*

📋 *Generated Student Information:*
• 👤 Name: {student_data['first_name']} {student_data['last_name']}
• 📧 Email: {student_data['email']}
• 🏫 University: {student_data['university']['name']}
• 🆔 Student ID: {student_data['student_id']}
• 🎂 Date of Birth: {student_data['birth_date']}

🖼️ *Document Generated:*
• Type: Student ID Card
• Size: {file_size / 1024:.1f} KB
• Format: PNG

⏱️ *Full Process Simulation:*
✅ Step 1: Information generated
✅ Step 2: University selected  
✅ Step 3: ID card created
✅ Step 4: Data validated
🔄 Step 5: Would submit to SheerID

📊 *Real Process Includes:*
• SheerID API communication
• Document upload
• Automatic form filling
• Status tracking

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
📚 *How to Use This Bot - Complete Guide*

🔗 *Real Verification (with SheerID link):*
1. Get verification link from service (Google One, Spotify, etc.)
2. Use /verify command or click "Start Verification"
3. Paste the SheerID link
4. Bot automatically:
   • Extracts verification ID
   • Generates student data
   • Creates ID card image
   • Submits to SheerID API
   • Uploads document

🎮 *Quick Simulation (without link):*
1. Use /simulate command
2. See complete process demonstration
3. View generated student ID card

📋 *SheerID Link Format:*
The link should look like:
`https://services.sheerid.com/verify/...?verificationId=...`

🛠️ *Technical Features:*
• Real SheerID API integration
• Pillow image generation
• HTTPX for API requests
• Automatic form submission
• Document upload

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
🤖 *Bot Status Report - Complete Automation*

✅ *Status:* Online and Operational
🕒 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 *Server:* Render.com Web Service
📊 *Version:* 4.0 Full Automation
🔧 *Mode:* Real SheerID API Integration

📈 *Automation Features:*
• ✅ SheerID API communication
• ✅ Pillow document generation
• ✅ Automatic data submission
• ✅ Document upload system
• ✅ University database: {len(UNIVERSITIES)} schools

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
    
    # Answer the callback query
    query.answer()
    
    if query.data == "start_real_verify":
        query.edit_message_text(
            "🔗 *Real SheerID Verification*\n\n"
            "📝 *Please send your SheerID verification link:*\n\n"
            "The link should look like:\n"
            "`https://services.sheerid.com/verify/...?verificationId=...`\n\n"
            "*Or type /cancel to stop*",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_URL
        
    elif query.data == "quick_simulate":
        simulate_command(update, context)
        
    elif query.data == "show_help":
        help_command(update, context)
        
    elif query.data == "main_menu":
        start_command(update, context)
        
    elif query.data == "show_stats":
        stats_text = """
📊 *Statistics Feature Coming Soon!*

🚀 *Currently active features:*
• Real SheerID API integration
• Automatic document generation
• Complete verification automation

📈 *Planned updates:*
• User verification history
• Success rate tracking
• University performance analytics
• Multi-language support

💡 *Use /verify to start a real verification now!*
        """
        query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

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
            entry_points=[
                CommandHandler('verify', verify_command),
                CallbackQueryHandler(button_handler, pattern='^start_real_verify$')
            ],
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
        
        # Add button handler for other buttons
        dispatcher.add_handler(CallbackQueryHandler(button_handler, 
            pattern='^(quick_simulate|show_help|main_menu|show_stats)$'))
        
        # Add message handler for other messages
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, 
            lambda update, context: update.message.reply_text(
                "💡 Use /verify to start real verification or /help for instructions."
            )))
        
        # Log successful setup
        logger.info("✅ Bot setup completed successfully with full SheerID automation")
        print("=" * 50)
        print("🤖 Telegram Bot with Complete SheerID Automation")
        print(f"🔑 Token: {BOT_TOKEN[:10]}...")
        print(f"🌐 HTTP Port: {PORT}")
        print(f"🎓 Universities: {len(UNIVERSITIES)}")
        print(f"🔗 SheerID API: {SHEERID_API_URL}")
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
    print("🚀 Telegram Bot with Complete SheerID Automation")
    print("🔗 Real API Integration + Document Generation + Auto-Submission")
    print("=" * 60)
    
    # Start HTTP server in background thread
    print("🌐 Starting HTTP server for health checks...")
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    print(f"✅ HTTP server started on port {PORT}")
    
    # Setup and start Telegram bot
    print("\n🤖 Setting up Telegram bot with full SheerID automation...")
    updater = setup_bot()
    
    if updater:
        try:
            print("🚀 Starting bot polling...")
            updater.start_polling()
            print("✅ Bot is now running with complete automation!")
            print("📱 Send /verify with your SheerID link for real verification")
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