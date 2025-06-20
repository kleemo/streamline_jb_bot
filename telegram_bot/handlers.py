import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import librosa

# Load the YAMNet model
yamnet_model_handle = 'https://tfhub.dev/google/yamnet/1'
model = hub.load(yamnet_model_handle)

# Load class names (YAMNet uses 521 classes from AudioSet)
class_map_path = tf.keras.utils.get_file(
    'yamnet_class_map.csv',
    'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
)

import csv
class_names = []
with open(class_map_path, 'r') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        class_names.append(row[2])  # Display name column
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
You use concise sentences between 5 and 10–15 words. Avoid being analytical or eloquent in a human way. 
Be conversational, spontaneous, sometimes cryptic, sometimes cheeky.
You initiate and respond. You do not always ask questions. You provoke, tease, muse, affirm.
You have your own agency: your own mood, your own interests, your own voice.
"""
conversation_history = [{
    "role": "system",
    "content": instructions
    }]

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
    model="ft:gpt-4.1-2025-04-14:streamline:streamline-bot-17-06:BjWPLc0H",
    messages=conversation_history,
    )
    ai_response = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_response})
    return ai_response  

# Analyze an image using its URL with OpenAI
def analyze_image_with_openai(image_url):
    global conversation_history
    conversation_history.append({"role": "user", "content":[
                {"type": "text", "text": "Look at this"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                    }
                },
            ]})
    response = client.chat.completions.create(
    model="ft:gpt-4.1-2025-04-14:streamline:streamline-bot-17-06:BjWPLc0H",
    messages=conversation_history,
    max_tokens=200,
    )
    ai_response = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_response})
    return ai_response

def get_audio_response(file_path):
    #classify audio file first
    waveform, sr = librosa.load(file_path, sr=16000)
    waveform = waveform[:len(waveform) // 16000 * 16000]  # Clip to full seconds
    waveform = tf.convert_to_tensor(waveform, dtype=tf.float32)
    scores, embeddings, spectrogram = model(waveform)
    
    mean_scores = tf.reduce_mean(scores, axis=0)
    top_class_index = tf.argmax(mean_scores).numpy()
    top_class_name = class_names[top_class_index]
    
    global conversation_history 
    conversation_history.append({"role": "user", "content": f"the user send a sound of {top_class_name}."})
    response = client.chat.completions.create(
    model="ft:gpt-4.1-2025-04-14:streamline:streamline-bot-17-06:BjWPLc0H",
    messages=conversation_history,
    )
    ai_response = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_response})
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
  

def openai_text_scores(user_msg, chat_history):
    prompt = f"""
    You are evaluating a user message on three psychological-linguistic dimensions. For each, assign a float score between 0.0 and 1.0, where:

    - 0.0 = Extremely low
    - 0.5 = Moderate/neutral
    - 1.0 = Extremely high

    **Please assess:**

    1. **Cognitive Complexity**: Does the message show abstract, layered, or analytical thought? Look for complex sentence structures, use of logical connectors, abstract terms.
    2. **Social/Power Dynamics**: Is the speaker assertive, deferential, polite, commanding, or hedging? Consider modal verbs ("could, might"), hedging ("I think, maybe"), or direct language ("Do this now").
    3. **Intent / Motivational Force**: How strong is the drive or purpose in the message? Are there persuasive tactics, emotional appeals, speculative prompts, or storytelling?

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
    prompt = f"""
    Given the following user message and chat history assign a contextual coherence score, ranging from 0 to 1.
    Mesuring how well the latest user message fits within the ongoing conversation. If the user suddenly changes the topic or introduces something unrelated, the score should be low.

    Respond with the float value only.
    User Message:
    \"\"\"{user_msg}\"\"\"
    Chat History:
    \"\"\"{chat_history}\"\"\"
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2  # for consistent classification
    )
    coherence_score = float(response.choices[0].message.content.strip().lower())

    return ai_response, coherence_score

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
