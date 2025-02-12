import requests
import os
from dotenv import load_dotenv
import openai
# Load environment variables from .env file
load_dotenv()
# Telegram Bot API token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

openai.api_key = os.getenv('OPENAI_API_KEY')
    

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
        
        return file_url  # Return image url
    return None

def get_openai_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # You can also use "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a good friend."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=150,  # Controls response length
        temperature=0.9, # Controls randomness (0 = deterministic, 1 = more creative)
    )
    return response.choices[0].message['content']    

# Analyze an image using its URL with OpenAI
def analyze_image_with_openai(image_url):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "A friend send you this image and you want to get the location."},
                {
                    "role": "user",
                    "content": f"Reactt to the image",
                    "attachments": [{"type": "image_url", "url": image_url}]
                }
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error analyzing the image: {e}"
