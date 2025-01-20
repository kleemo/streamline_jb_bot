from flask import Flask, render_template, request
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import requests

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
        text = update['message']['text']
        print(f"Received message from {chat_id}: {text}")

        # Example: Echo the user's message back
        send_message_to_telegram(chat_id, f"You said: {text}")

    return '', 200  # Respond with a 200 status to acknowledge the update

def send_message_to_telegram(chat_id, text):
    
    #Send a message to a Telegram chat using the Telegram Bot API.
    
    url = f'{TELEGRAM_API_URL}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)

@socketio.on('connecting')
def handle_my_custom_event(json):
    print('received json: ' + str(json))


# entry point when running the app. Must be called at the end of the script
if __name__ == '__main__':
    socketio.run(app)

