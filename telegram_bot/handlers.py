import requests
import os
from dotenv import load_dotenv
from .utils import image_encoder
# Load environment variables from .env file
load_dotenv()
# Telegram Bot API token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def telegram_webhook(request):

    #Endpoint to receive updates from Telegram.
    
    update = request.json  # Get the JSON payload from Telegram
    if 'message' in update:
        chat_id = update['message']['chat']['id']

        if "text" in update["message"]:
            text = update['message']['text']
            print(f"Received message from {chat_id}: {text}")
            send_message_to_telegram(chat_id, f"You said: {text}")

        if "photo" in update["message"]:
            print("photo received")
            photo_sizes = update["message"]["photo"]  # List of photo sizes
            file_id = photo_sizes[-1]["file_id"]
            file_url = fetch_image(file_id)
            encoded_file = image_encoder(file_url)
            arr_str = "\n".join(map(str, encoded_file))
            send_message_to_telegram(chat_id,"you send a photo: " + arr_str )
        

    return '', 200  # Respond with a 200 status to acknowledge the update

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
    
        return file_url  # Return image urls
    return None