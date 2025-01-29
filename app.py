from flask import Flask, render_template, request
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import requests
from skimage.io import imread
from skimage.transform import resize
import numpy as np
import joblib

# Load environment variables from .env file
load_dotenv()
# Telegram Bot API token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def telegram_webhook():

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
            file_param = fetch_image(file_id)
            arr_str = "\n".join(map(str, file_param))
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

        img = imread(file_url, as_gray=True)
        print("imgage loaded ")
        # Resize the image
        original_height, original_width = img.shape
        max_size = 64
        scaling_factor = max(max_size / original_height, max_size / original_width)
        new_height = int(original_height * scaling_factor)
        new_width = int(original_width * scaling_factor)
        img = resize(img, (new_height+1, new_width+1), anti_aliasing=True)
        img = img[0:64,0:64]
        print("imgage resized")
        print(img.shape)
        flatten_img = img.flatten()
        print(flatten_img.shape)
        if flatten_img.shape != (4096,):
            return "image wrong dimensions"
        
        new_data = [flatten_img,flatten_img]
        rbm = joblib.load("models\model_rbm_images.pkl")
        transformed_data = rbm.transform(new_data)
        print("data transformed")
        #print(transformed_data[0])
        


        return transformed_data[0]  # Return the saved file path
    return None

@socketio.on('connecting')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

# entry point when running the app. Must be called at the end of the script
if __name__ == '__main__':
    socketio.run(app)

