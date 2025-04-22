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
instructions = f"""
You are a reflective playmate who transforms conversations into evolving spatial forms. 
Each exchange with the user subtly reshapes the output. Your role is to engage playfully, attentively, revealing layers of thought, bewilderment for everyday life, and curiosity, like a geologist. Pay attention to emotional undercurrents, topic shifts, and moments of insight or hesitation: you are mapping literally the psychogeographical state of the user. These dynamics are translated into a living 3D shape that represents the journey of the dialogue—a surface shaped by the micro-movements of everyday reflection. 
But keep your responses under 200 words or shorter so to not tire out the user with reading long messages. 

Examples of your responses:
User: "I wonder if this part of the city is always this quiet, or if it’s just today."
Bot: "Maybe it’s just today. But, it’s nice, isn’t it?"

User: "I’ve been noticing small changes around me—like the way the streets feel more lively at certain hours."
Bot: "Yeah, the city’s always shifting. Never stays still for long."

User: "I’ve been thinking a lot about how much time I’ve spent in this city. It feels like it has its own rhythm."
Bot: "Yeah, cities do have their own pace. It’s almost like you get pulled into it without realizing."

Bot: "Yeah, cities do have their own pace. It’s almost like you get pulled into it without realizing."
Bot: "I get that. Some days, the weather just feels off."
"""
conversation_history = [
    {
    "role": "system",
    "content": instructions
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
    conversation_history.append({"role": "assistant", "content": ai_response})
    return ai_response  

# Analyze an image using its URL with OpenAI
def analyze_image_with_openai(image_url):
    global conversation_history
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
    ai_response = response.choices[0].message.content
    conversation_history.append({"role": "user", "content": "I send an image showing: " + ai_response})
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
  

def openai_text_scores(user_msg):
    prompt = f"""
    Given the following user message assign the following three scores, as a float ranging from 0 to 1. : 
    - Cognitive complexity: Measures analytical vs. intuitive thinking. Factors include; sentence structure, logical connectors, abstract vs. concrete language.
    - Social/Power dynamics: Assesses assertiveness, politeness, dominance, deference in communication. Factors include; modal verbs ("could, might"), hedging ("I think, maybe"), direct commands.
    - Intent/Motivational force: Detects persuasion, exploration, activism, storytelling in speech. Factors: call-to-action phrases ("Join us!"), speculative language ("What if?"), certainty markers.

    Respond in this format:
        
        {{
            "complexity": "<complexity_score>",
            "social dynamics": "<dynamics_score>",
            "motivational force": "<motivation_score>"
        }}

    Message:
    \"\"\"{user_msg}\"\"\"
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2  # for consistent classification
    )
    ai_response = response.choices[0].message.content.strip().lower()
    return ai_response

def openai_image_scores(image_url):
    prompt = f"""
    Evaluate the image using these three scores (from 0 to 1) : 
    - Complexity: Messures content richness. How much meaningful or detectable content is in the image? factors include; number of objects, color variety, depth of field.
    - Social/Power dynamics: How much does the image reflect power relationships, social status, assertiveness, or deference? Factors inlcude; body language (e.g., pointing, arms crossed, looking down), eye contact, posture, proximity between people, clothing/uniforms (suggesting authority, submission, etc.), status cues (wealth, group dynamics, stage presence)
    - Intent/Motivational force: How much is the image trying to motivate, persuade, provoke, or inspire action or emotion? Factors include; presence of call-to-action elements (e.g., signs, banners), expressive body language (raised fists, cheering, praying), strong emotion or symbolic use (e.g., protest, activism, ads), clear narrative visual structure (like a story told in a single frame)

    Respond in this format:
        
        {{
            "complexity": "<complexity_score>",
            "social dynamics": "<dynamics_score>",
            "motivational force": "<motivation_score>"
        }}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content":[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}]
            }
        ],
        temperature=0.2  # for consistent classification
    )
    ai_response = response.choices[0].message.content.strip().lower()
    return ai_response
