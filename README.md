# Overview
This project builds upon the existing work Streamlines of Otherness https://freeradicals.io/projects/streamlines-of-otherness/ and is realized in collaboration with Joelle Bitton.
The application allows the user to generate 3D printed clay objects by interacting with a Telegram chatbot.

 Table of Contents
- [Technology Stack](#technology-stack)
  - [Backend](#backend)
  - [Webhook](#webhook)
  - [API integration](#api-integration)
  - [3D printer communication](#3d-printer-communication)
- [3D Simulation](#3d-simulation)
- [Setup](#setup)
  - [Environment variables](#environment-variables)
  - [Create environment and install requierements](#create-environment-and-install-requierements)
- [AI Scores](#ai-scores)
  - [Supported Scores](#supported-scores)
  - [Adding Custom Scores](#adding-custom-scores)
  - [Mapping AI Scores to Printing Parameters](#mapping-ai-scores-to-printing-parameters)
- [Printing Parameters](#printing-parameters)
  - [General Settings](#general-settings)
  - [Shape Parameters](#shape-parameters)
  - [Line Parameters](#line-parameters)
- [Telegram Bot](#telegram-bot)
  - [Fine-tune Model with Examples](#fine-tune-model-with-examples)
- [Future Work](#future-work)
  - [Multiple users](#multiple-users)
  - [Storing outcomes for model training](#storing-outcomes-for-model-training)

# Technology Stack
## Backend
Flask unsing SocketIO to communicate with the frontend. 
## Webhook
The application recieve updates from the chatbot through a webhook. 
## API integration
For chat text classification and completion we use the openAI API. 
To send text messages back to the user we use the Telegram API.
## 3D printer communication
To communicate with the 3D printer Printrund suite https://github.com/kliment/Printrun was used.

# 3D Simulation
For testing during developing and documentation you can view some of the generated 3d shape on this website: https://spectacular-hotteok-47e6cf.netlify.app/

# Setup
## environment variables
1. Rename the example_env.txt file to .env
2. copy paste the open ai API key from the project website into the .env file https://platform.openai.com/settings/proj_LPoMKnZhBYYVyKUUVGr1UXAF/api-keys
3. create a new telegram bot or use an existing bot and copy paste the bot token into the .env file https://core.telegram.org/bots/tutorial 
## Create environment and install requierements
see instrucion of previous version (link)

# AI Scores
## Supported Scores
include text embedding vectors explenation (link)
## Adding Custom Scores
## Mapping AI Scores to Printing Parameters

# Printing Parameters
## General Settings
## Shape Parameters
## Line Parameters

# Telegram Bot
## Fine-tune Model with Examples

# Future Work
## Multiple users
## Storing outcomes for model training