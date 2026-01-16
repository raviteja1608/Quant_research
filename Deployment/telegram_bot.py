"""
Telegram Bot Module
Provides functions to send messages to Telegram bot and group chat.

This module can be imported by other scripts or run standalone for testing.
"""

import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = "8581377867:AAFq38EMHvfZJCNI7dAQay1kq90i2j1BaSk"
CHAT_ID_BOT = "8528872039"      # Personal bot chat ID
CHAT_ID_GROUP = "-5162841655"   # Group chat ID


def send_telegram_bot(message, parse_mode=None):
    """
    Send a message to the personal Telegram bot.
    
    Args:
        message (str): Message text to send
        parse_mode (str): Optional parse mode ('Markdown', 'MarkdownV2', or 'HTML')
    
    Returns:
        dict: Response from Telegram API
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID_BOT,
        "text": message
    }
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logger.info(f"Message sent successfully to bot (chat_id: {CHAT_ID_BOT})")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to bot: {e}")
        return {"ok": False, "error": str(e)}


def send_telegram_group(message, parse_mode=None):
    """
    Send a message to the Telegram group chat.
    
    Args:
        message (str): Message text to send
        parse_mode (str): Optional parse mode ('Markdown', 'MarkdownV2', or 'HTML')
    
    Returns:
        dict: Response from Telegram API
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID_GROUP,
        "text": message
    }
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logger.info(f"Message sent successfully to group (chat_id: {CHAT_ID_GROUP})")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to group: {e}")
        return {"ok": False, "error": str(e)}


def send_telegram(message, target='group', parse_mode=None):
    """
    Unified function to send message to bot or group.
    
    Args:
        message (str): Message text to send
        target (str): 'bot' or 'group' (default: 'group')
        parse_mode (str): Optional parse mode ('Markdown', 'MarkdownV2', or 'HTML')
    
    Returns:
        dict: Response from Telegram API
    """
    if target.lower() == 'bot':
        return send_telegram_bot(message, parse_mode)
    else:
        return send_telegram_group(message, parse_mode)


if __name__ == "__main__":
    # Test messages when run standalone
    print("Telegram Bot Module - Testing")
    print("=" * 60)
    
    test_message = "🤖 Test message from Telegram Bot Module\n\nThis is a test to verify the module is working correctly."
    
    print("\nSending test message to group...")
    result = send_telegram_group(test_message)
    
    if result.get('ok'):
        print("✓ Test message sent successfully!")
    else:
        print(f"✗ Test message failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("Module is ready to be imported by other scripts.")
