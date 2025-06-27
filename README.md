# Overview
This project builds upon the existing work [Streamlines of Otherness](https://freeradicals.io/projects/streamlines-of-otherness/) and is realized in collaboration with Joelle Bitton.
The application allows users to generate 3D printed clay objects by interacting with a Telegram chatbot.

## Table of Contents
- [Overview](#overview)
- [Technology Stack](#technology-stack)
  - [Backend](#backend)
  - [Webhook](#webhook)
  - [API Integration](#api-integration)
  - [3D Printer Communication](#3d-printer-communication)
- [3D Simulation](#3d-simulation)
- [Setup](#setup)
  - [Environment Variables](#environment-variables)
  - [Create Environment and Install Requirements](#create-environment-and-install-requirements)
- [AI Scores](#ai-scores)
  - [Supported Scores](#supported-scores)
  - [Adding Custom Scores](#adding-custom-scores)
  - [Mapping AI Scores to Printing Parameters](#mapping-ai-scores-to-printing-parameters)
- [Printing Parameters](#printing-parameters)
  - [General Settings](#general-settings)
- [Geometry Taxonomy](#geometry-taxonomy)
  - [Shape Parameters](#shape-parameters)
  - [Line Parameters](#line-parameters)
- [Telegram Bot](#telegram-bot)
  - [Fine-tune Model with Examples](#fine-tune-model-with-examples)
- [Future Work](#future-work)
  - [Multiple Users](#multiple-users)
  - [Storing Outcomes for Model Training](#storing-outcomes-for-model-training)

# Technology Stack
## Backend
Flask using SocketIO to communicate with the frontend.

## Webhook
The application receives updates from the chatbot through a webhook. When deploying the application on localhost, ngrok is used to expose the webhook.

## API Integration
For chat text classification and completion, we use the OpenAI API. 
To send text messages back to the user, we use the Telegram API.

## 3D Printer Communication
To communicate with the 3D printer, [Printrun suite](https://github.com/kliment/Printrun) was used.

# 3D Simulation
For testing during development and documentation, you can view some of the generated 3D shapes on this website: https://spectacular-hotteok-47e6cf.netlify.app/

# Setup
## Environment Variables
1. Rename the `example_env.txt` file to `.env`.
2. Copy and paste the OpenAI API key from the project website into the `.env` file: https://platform.openai.com/settings/proj_LPoMKnZhBYYVyKUUVGr1UXAF/api-keys
3. Create a new Telegram bot or use an existing bot and copy and paste the bot token into the `.env` file: https://core.telegram.org/bots/tutorial 

## Create Environment and Install Requirements
See instructions from the previous version: [flask-socketio-printer](https://github.com/criseone/flask-socketio-printer)

## Webhook Exposure with ngrok
When running the application for the first time and trying to connect to the chatbot, an authentication error will occur. To resolve this error, an account at https://ngrok.com/ is needed.

# AI Scores
The application mainly uses the OpenAI GPT-4o model for extracting pre-defined scores from text, images, and GPS locations. As of now, GPT-4o does not support audio processing; therefore, a TensorFlow model is used to extract information from audio files.

## Supported Scores
Implemented scores (excluding audio scores) are listed in the `telegram_bot/ai_scores.json` file. Each score belongs to one of two types:
- **Categorical scores:** Given a list of possible categories, the model returns the most fitting ones.
- **Numeric scores:** According to the prompt, the model assigns a float value between 0 and 1.

In addition to the described scores, the application also supports extraction of feature vectors from text (text embedding): https://platform.openai.com/docs/guides/embeddings/embedding-models

## Adding Custom Scores
*Note: At the moment, it is not possible to add custom scores for audio files.*

Modification of existing scores and adding additional custom scores should be done in the `telegram_bot/ai_scores.json` file and should follow the structure below. No additional code modification is needed. The application iterates through the JSON file and prepares the requests for the GPT-4o model in the `telegram_bot/handlers.py` file.

```json
"name of the score (unique)": {
    "description": "prompt for the model",
    "type": "categorical or numeric", // for location score, numeric is not supported
    "categories": [] // only include if type is categorical
}
```

## Mapping AI Scores to Printing Parameters

# Printing Parameters
Start of the height depends on the plate.

## General Settings

# Geometry Taxonomy
See Google Sheet for reference.

## Shape Parameters

## Line Parameters

# Telegram Bot
## Fine-tune Model with Examples

# Future Work
## Multiple Users

## Storing Outcomes for Model Training