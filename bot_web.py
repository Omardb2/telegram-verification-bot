import os
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Updater, CommandHandler
import socket

# ============ HTTP Server for Render Health Checks ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle health check requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is alive')
    
    def log_message(self, format, *args):
        """Disable access logs"""
        pass

def start_http_server(port=8080):
    """Start HTTP server for Render health checks"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        print(f"✅ HTTP Server started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ HTTP Server error: {e}")

# ============ Telegram Bot ============
def start_telegram_bot():
    """Start the Telegram bot"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not set in environment variables")
        print("💡 Go to Render Dashboard → Environment → Add BOT_TOKEN")
        return
    
    try:
        # Initialize bot
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Command handlers
        def start_command(update, context):
            user = update.effective_user
            update.message.reply_text(
                f"👋 Hello {user.first_name}!\n"
                f"✅ Bot is working on Render\n"
                f"🕒 Server time: {time.strftime('%H:%M:%S')}"
            )
        
        def status_command(update, context):
            update.message.reply_text("✅ Bot status: Online and running!")
        
        # Add handlers
        dp.add_handler(CommandHandler("start", start_command))
        dp.add_handler(CommandHandler("status", status_command))
        dp.add_handler(CommandHandler("help", status_command))
        
        # Start bot
        print("🤖 Starting Telegram Bot...")
        print(f"🔑 Token: {BOT_TOKEN[:10]}...")
        updater.start_polling()
        print("✅ Telegram Bot is running!")
        
        # Keep bot running
        updater.idle()
        
    except Exception as e:
        print(f"❌ Telegram Bot error: {str(e)[:200]}")

# ============ Main Function ============
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Render-Compatible Telegram Bot")
    print("=" * 50)
    
    # Check for BOT_TOKEN
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN or BOT_TOKEN == "PLACEHOLDER":
        print("⚠️ WARNING: Using placeholder token")
        print("   Bot will not connect to Telegram")
        print("   Add real BOT_TOKEN in Render Environment Variables")
    
    # Start HTTP server in background thread (for Render health checks)
    print("🌐 Starting HTTP server for Render health checks...")
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    print("✅ HTTP server started in background")
    
    # Start Telegram bot in main thread
    print("\n" + "=" * 50)
    start_telegram_bot()
