# Telegram SheerID Verification Bot

Complete automation bot for SheerID student verification.

## Features
- ✅ Real SheerID API integration
- ✅ Automatic student data generation
- ✅ Student ID card generation with Pillow
- ✅ Complete form submission
- ✅ Document upload automation
- ✅ Web service health checks

## How It Works
1. User sends SheerID verification link
2. Bot extracts verification ID
3. Generates realistic student data
4. Creates student ID card image
5. Submits data to SheerID API
6. Uploads document automatically

## Deployment on Render
1. Connect GitHub repository
2. Set environment variables:
   - `BOT_TOKEN`: Telegram bot token
   - `PORT`: 8080
3. Deploy as Web Service

## Commands
- `/start` - Welcome message
- `/verify` - Start real verification
- `/simulate` - Quick simulation
- `/help` - Instructions
- `/status` - Bot status
