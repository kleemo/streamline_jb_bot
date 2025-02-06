import requests
import os
from dotenv import load_dotenv
from .utils import image_encoder, check_location
# Load environment variables from .env file
load_dotenv()
# Telegram Bot API token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
    

def send_message_to_telegram(chat_id, text):
    
    #Send a message to a Telegram chat using the Telegram Bot API.
    
    url = f'{TELEGRAM_API_URL}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)

def fetch_image(file_id):
    """Fetches and downloads an image from Telegram servers."""
    # Get file path from Telegram API
    file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
    file_info = requests.get(file_info_url).json()

    if "result" in file_info:
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        encoded_file = image_encoder(file_url)
        return encoded_file  # Return encoded image
    return None