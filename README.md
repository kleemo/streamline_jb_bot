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
### Backend
Flask using SocketIO to communicate with the frontend.

### Webhook
The application receives updates from the chatbot through a webhook. When deploying the application on localhost, ngrok is used to expose the webhook.

### API Integration
For chat text classification and completion, we use the OpenAI API. 
To send text messages back to the user, we use the Telegram API.

### 3D Printer Communication
To communicate with the 3D printer, [Printrun suite](https://github.com/kliment/Printrun) was used.

# 3D Simulation
For testing during development and documentation, you can view some of the generated 3D shapes on this website: https://spectacular-hotteok-47e6cf.netlify.app/

# Setup
### Environment Variables
1. Rename the `example_env.txt` file to `.env`.
2. Copy and paste the OpenAI API key from the project website into the `.env` file: https://platform.openai.com/settings/proj_LPoMKnZhBYYVyKUUVGr1UXAF/api-keys
3. Create a new Telegram bot or use an existing bot and copy and paste the bot token into the `.env` file: https://core.telegram.org/bots/tutorial 

### Create Environment and Install Requirements
See instructions from the previous version: [flask-socketio-printer](https://github.com/criseone/flask-socketio-printer)

### Webhook Exposure with ngrok
When running the application for the first time and trying to connect to the chatbot, an authentication error will occur. To resolve this error, an account at https://ngrok.com/ is needed.

### Changing connection port
The port and baud rate for connecting to the printer should be changed in the app.py file and in the static/vue_instance.js file. 

# AI Scores
The application mainly uses the OpenAI GPT-4o model for extracting pre-defined scores from text, images, and GPS locations. As of now, GPT-4o does not support audio processing; therefore, a TensorFlow model is used to extract information from audio files.

### Supported Scores
Implemented scores (excluding audio scores) are listed in the `telegram_bot/ai_scores.json` file. Each score belongs to one of two types:
- **Categorical scores:** Given a list of possible categories, the model returns the most fitting ones.
- **Numeric scores:** According to the prompt, the model assigns a float value between 0 and 1.

In addition to the described scores, the application also supports extraction of feature vectors from text (text embedding): https://platform.openai.com/docs/guides/embeddings/embedding-models

### Adding Custom Scores
*Note: At the moment, it is not possible to add custom scores for audio files.*

Modification of existing scores and adding additional custom scores should be done in the `telegram_bot/ai_scores.json` file and should follow the structure below. No additional code modification is needed. The application iterates through the JSON file and prepares the requests for the GPT-4o model in the `telegram_bot/handlers.py` file.

```json
"name of the score (unique)": {
    "description": "prompt for the model",
    "type": "categorical or numeric", // for location score, numeric is not supported
    "categories": [] // only include if type is categorical
}
```

### Mapping AI Scores to Printing Parameters
Mapping the retrieved ai scores to a shape or line parameter can be done in the telegram_bot/parametershandler.py file. All the possible parameters are listed at the top of the file and are also further described in the Geometry Taxonomy section. When receiving messages from the user through the chatbot the application calls a method in the parametershandler.py file depending on the type of the recieved message. Each method then calls the function to extract the ai socres and may also extract additional information about the input, for example pixel brightness for messages of type image.

Example 1: mapping the diameter of the second center point to the pixel brighness of an image. In the set_parameters_imgInput add:
```python
if len(self.shape_options["diameter"]) >= 2:  # Make sure we have at least 2 center points
    max_diameter = max(self.shape_options["diameter"][1][0], self.shape_options["diameter"][1][1]) + 40
    min_diameter = min(80, max_diameter) - 80
    # Helper function to map the range of brightness (0-1) to the desired range
    new_diameter = self.map_parameter_to_range(avg_brightness, min_diameter, max_diameter, 0, 1)
    self.shape_options["diameter"][1][0] = new_diameter  # Assign x-diameter of the 2nd center point
    self.shape_options["diameter"][1][1] = new_diameter  # Assign y-diameter of the 2nd center point
```

Example 2: mapping a line pattern to the location category. In the set_parameters_locationInput add:
```python
location_category = scores.get("location_category", "none")  # none is the default value if not found
if location_category == "urban":
    self.line_options["pattern"] = "rect"
```
### Fine-tune the model with scoring examples

# Printing Parameters
- Starting height: Can be set in the slicerhandler.py file at the very top.
- E (often refered to as extrusion rate) controls how much filament is extruded. Standard value is around 0.8 for more wetter clay or when the pressure is high use slighly higher values.
- F (often refered to as extrusion rate) controls how fast the x,y move happens, and cansequenctly also how fast the extrusion happens. Here as well increase slighly when the clay is wetter. A good starting value is around 1200.
- New/Home button brings the printer head back to its home position and resets the layer count to 0. But does not reset any other values.

# Geometry Taxonomy
*Note: Also see google sheet for reference*

### Shape Parameters

### Line Parameters

# Telegram Bot
To improve the behaviour of the chat bot a usefule technique is to fine-tune an allready trained model like gpt-o https://platform.openai.com/docs/guides/fine-tuning
### Fine-tune Model with Examples

# Future Work
### Multiple Users

### Storing Outcomes for Model Training