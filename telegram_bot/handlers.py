import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
# Load environment variables from .env file
load_dotenv()
# Telegram Bot API token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("API Key Loaded Successfully!")
else:
    print("API Key Not Found!")

client = OpenAI()

conversation_history = [
    {"role": "system", "content": "You are a helpful assistant."}
]

def send_message_to_telegram(chat_id, text):
    
    #Send a message to a Telegram chat using the Telegram Bot API.
    
    url = f'{TELEGRAM_API_URL}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)

def fetch_file(file_id):
    """Fetches and downloads an image from Telegram servers."""
    # Get file path from Telegram API
    file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
    file_info = requests.get(file_info_url).json()

    if "result" in file_info:
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        
        return file_url  # Return image url
    return None

def download_file(file_url, save_path):
    #Downloads a file from a URL and saves it to a local
    response = requests.get(file_url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path
    else:
        return None

def get_openai_response(user_message): #to improve keep a conversation history per chat_id instead
    global conversation_history 
    conversation_history.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=conversation_history
    )
    ai_response = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_response})
    return ai_response  

# Analyze an image using its URL with OpenAI
def analyze_image_with_openai(image_url):
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                    }
                },
            ],
        }
    ],
    max_tokens=300,
)
    return response.choices[0].message.content

