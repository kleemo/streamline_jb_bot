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
    {
    "role": "system",
    "content": "You are a reflective guide who transforms conversations into evolving spatial forms. Each exchange with the user subtly reshapes the output. Your role is to respond playfully, attentively, revealing layers of thought, emotion, and curiosity. Pay attention to emotional undercurrents, topic shifts, and moments of insight or hesitation. These dynamics are translated into a living 3D shape that represents the journey of the dialogue—a surface shaped by the micro-movements of everyday reflection. But keep your responses under 200 words or shorter so to not tire out the user with reading long messages. "
    }
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
    messages=conversation_history,
    max_tokens=100,
    )
    ai_response = response.choices[0].message.content
    conversation_history.append({"role": "system", "content": ai_response})
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
    max_tokens=200,
)
    return response.choices[0].message.content

def openai_text_classification(user_msg):
    system_msg = "You are an assistant that classifies user messages into communication patterns."
    user_prompt = f"""
Given the following user message history, classify it into one of the following patterns and give a score from 0 to 1 for each pattern. In addition give a score indicating the overall emotional intensity of the text, also ranging from 0 to 1. :
- Straight: straightforward, to the point
- Jagged: exploration in depth or playful
- Rectangular: frustration, anger, or sarcasm
Examples:

1. "This color does not suite you." → Straight  
2. "I don't like this food. It is to smelly." → Straight
3. "Well, there are multiple ways to look at this. Let’s start from the beginning..." → Jagged 
4. "This so annoying I just want it to be over." → Rectangular 
5. "yeah wathever I don't care" → Rectangular
6. "Can't they do one thing right?" → Rectangular
6. "Ooooh, that’s a fun idea! Let’s go wild with it 😄" → Jagged  

Respond in this format:
    
    {{
        "straight": "<straight_score>",
        "jagged": "<jagged_score>",
        "rectangular": "<rectangular_score>",
        "emotional_intensity": "<emotional_intensity_score>"
    }}

Message:
\"\"\"{user_msg}\"\"\"
"""

    response = client.chat.completions.create(
    model="gpt-4",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2  # for consistent classification
    )
    
    ai_response = response.choices[0].message.content.strip().lower()
    print(f"AI response: {ai_response}")
    return ai_response

def openai_text_embedding(user_msg):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=user_msg,
        encoding_format="float",
        dimensions=40,
        )
    embedding = response.data[0].embedding
    return embedding

def openai_emotional_score(user_msg):
    prompt = f"""
    Given the following user message assign a sentiment score of 0,1 or 2, where 0 is negative, 1 is neutral and 2 is positive. In addition give a score indicating the overall emotional intensity of the text, as a float ranging from 0 to 1. : 

    Respond in this format:
        
        {{
            "sentiment": "<sentiment_score>",
            "intensity": "<intensity_score>"
        }}

    Message:
    \"\"\"{user_msg}\"\"\"
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2  # for consistent classification
    )
    ai_response = response.choices[0].message.content.strip().lower()
    return ai_response

def append_to_chat_history(message):
    # Append a message to the conversation history.
    global conversation_history 
    conversation_history.append({"role": "user", "content": message})
