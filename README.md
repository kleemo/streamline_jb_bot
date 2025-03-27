# Overview
This project builds upon the existing work Streamlines of Otherness https://freeradicals.io/projects/streamlines-of-otherness/ and is realized in collaboration with Joelle Bitton.
The application allows the user to generate 3D printed clay objects by interacting with a Telegram chatbot.

# The application
## Backend
Flask unsing SocketIO to communicate with the frontend. 
## Webhook
The application recieve updates from the chatbot through a webhook. 
## API integration
For chat text classification and completion we use the openAI API. 
To send text messages back to the user we use the Telegram API.
## 3D printer communication
To communicate with the 3D printer Printrund suite https://github.com/kliment/Printrun was used.
