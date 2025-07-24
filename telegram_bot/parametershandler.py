"""
parametershandler.py

This module defines the ParametersHandler class, which manages and updates
various parameters for a Telegram bot based on user input, including text,
images, audio, and location. It uses AI models to extract scores from inputs
and maps them to printing parameters for downstream use.

Dependencies:
    - joblib
    - numpy
    - math
    - json
    - skimage.io
    - librosa
    - os
    - telegram_bot.handlers (openai_text_embedding, openai_text_scores, openai_image_scores)
"""
import joblib
import numpy as np
import math
import json
from skimage.io import imread
import librosa
import os
from telegram_bot.handlers import openai_text_embedding, openai_text_scores, openai_image_scores, classify_audio

class ParametersHandler():
    """
    Handles the extraction, mapping, and management of parameters for the Telegram bot
    based on various user inputs (text, image, audio, location).

    Attributes:
        accumulated_chat (str): Accumulated conversation text (user and bot.)
        accumulated_user_text (str): Accumulated user-only text.
        num_input (int): Counter for the number of inputs received.
        filling (int): Placeholder for filling parameter.
        clip_fill_start (int): Placeholder for clip fill start.
        clip_fill_end (int): Placeholder for clip fill end.
        shape_options (dict): Parameters for shape.
        line_options (dict): Parameters for line.
        ai_scores (dict): Stores AI-evaluated scores for motivation, complexity, and coherence.
    """
    def __init__(self, pattern):
        """
        Initializes the ParametersHandler with default values and options.
        """
        self.accumulated_chat = ""
        self.accumulated_user_text = ""
        self.num_input = 0
        self.feature_vector = []
        self.filling = 0
        self.clip_fill_start = 0
        self.clip_fill_end = 0
        self.shape_options = { 
            "transition_rate":1,
            "base_shape": "circle",
            "diameter": [],
            "rotation": 0,
            "center_points": [(-40,50), (40,5),(-40,-30),(-30,20),(-10,-30)],
            "num_center_points": 4,
            "growth_directions": [(-40,50), (40,5),(-40,-30),(-30,20),(-10,-30)],
            "repetitions": 1,
            "free_hand_form":[],
        }
        self.line_options = {
            "pattern_range": 60,
            "pattern_start":50,
            "transition_rate":0.5,
            "pattern": "rect",
            "amplitude": 1,
            "frequency":1,
            "irregularity":0,
            "glitch": "none"
        }
<<<<<<< HEAD
        self.ai_scores = {
            "motivation_score": 0,
            "complexity_score": 0,
            "coherence_score": 0,
        }
=======
        self.z_plane = {
            "frequency": 20,
            "amplitude": 10,
            "non_planar": "no",
        }
        self.ai_scores = {}
>>>>>>> upstream/main

    def get_parameters(self):
        """
        Returns the current shape and line parameters.

        Returns:
            tuple: (shape_parameters, line_parameters, z_plane_parameters)
        """
        shape_parameters =  self.shape_options
        line_parameters = self.line_options
<<<<<<< HEAD
        return shape_parameters , line_parameters
          
=======
        z_plane_parameters = self.z_plane
        return shape_parameters , line_parameters, z_plane_parameters
        
>>>>>>> upstream/main
    def set_parameters_textInput(self, user_text = None):
        """
        Updates parameters based on user text input using AI model scores.

        Args:
            user_text (str, optional): The user's input text.
        """
        # Default scores if ai fails
        motivation_score = 0.5  
        dynamics_score = 0.5
        complexity_score = 0.5
        coherence_score = 0.5
        scores = "" #variable to store the scores the ai returns
        #get scores from ai model
        if user_text != None:
            scores, coherence = openai_text_scores(user_text, self.accumulated_chat)
            if self.accumulated_user_text == "":
                coherence_score = 0.5
            else:
                coherence_score = coherence
        # extract the individual scores from the scores object 
        try:
            scores = json.loads(scores)  # Parse the JSON string into a Python dictionary
            motivation_score = float(scores.get("motivational force", 0.5))
            dynamics_score = float(scores.get("social dynamics", 0.5))
            complexity_score = float(scores.get("complexity", 0.5))
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")

        #assign the ai scores to a corresponding line parameter
        self.line_options["amplitude"] = int(self.map_parameter_to_range(motivation_score, 1, 20, 0, 1))
        self.line_options["frequency"] = int(4 - int(self.map_parameter_to_range(complexity_score, 0, 3, 0, 1)))
        self.line_options["pattern_range"] = int(self.map_parameter_to_range(coherence_score, 0, 50, 0, 1))

        #update the ai scores to display in the UI
        self.ai_scores["motivation_score"] = motivation_score
        self.ai_scores["complexity_score"] = complexity_score
        self.ai_scores["coherence_score"] = coherence_score

    def set_parameters_imgInput(self, image_url=None):
        """
        Updates parameters based on image input using AI model scores and raw image analysis.

        Args:
            image_url (str, optional): Path or URL to the image file.
        """
        # Default scores if ai fails
        motivation_score = 0.5  
        dynamics_score = 0.5
        complexity_score = 0.5
        scores = "" #variable to store the scores the ai returns
        img = None#variable to store a pixel map of the image
        #get scores from ai model
        if image_url != None:
            scores = openai_image_scores(image_url)
            img = imread(image_url, as_gray=True)
        # extract the individual scores from the scores object 
        try:
            scores = json.loads(scores)  # Parse the JSON string into a Python dictionary
            motivation_score = float(scores.get("motivational force", 0.5))
            dynamics_score = float(scores.get("social dynamics", 0.5))
            complexity_score = float(scores.get("complexity", 0.5))
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")
        #extract extra information from the image, such as average brightness (pixel intensity ranges from 0 to 1)
        avg_brightness = np.mean(img)
        median_brightness = np.median(img)
        #assign the ai scores to a corresponding line parameter
        self.line_options["amplitude"] = int(self.map_parameter_to_range(motivation_score, 1, 20, 0, 1))
        self.line_options["frequency"] = int(4 - int(self.map_parameter_to_range(complexity_score, 0, 3, 0, 1)))

        #update the ai scores to display in the UI
        self.ai_scores["motivation_score"] = motivation_score
        self.ai_scores["complexity_score"] = complexity_score
    
    def set_parameters_audioInput(self,auid_file=None):
        """
        Updates parameters based on audio input by extracting audio features.

        Args:
            auid_file (str, optional): Path to the audio file.
        """
        #search for correct file
        input_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), auid_file)
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"File not found: {input_path}")
            
        y, sr = librosa.load(input_path, sr=None) #extract raw feature map of the audio
        #extract extra information from the audio, such as average loudness
        rms = librosa.feature.rms(y=y) # Root Mean Square Energy loudness of the audio
        print("audio loudnes: " + str(rms.mean()))
        #classify the sound. For all the possible audio classes see sound_classes.txt in the same folder
        sound_class = classify_audio(auid_file)
<<<<<<< HEAD
        print("audio file is the sound of " + sound_class)
=======
        #assign the ai scores to a corresponding line parameter

        #update the ai scores to display in the UI
        self.ai_scores["sound category"] = sound_class
>>>>>>> upstream/main

    def set_parameters_locationInput(self,location):
        """
        Updates parameters based on location input.
        maybe we should extend this to also extract informatin about the type of location (i.e. urban, forest...)

        Args:
            location (dict): Dictionary with 'longitude' and 'latitude' keys.
        """
        #extract information from location
        long= location["longitude"]
        lat = location["latitude"]
<<<<<<< HEAD
=======
        #get scores from ai model
        scores = openai_location_scores(lat,long)
        #assign the ai scores to a corresponding line parameter

        #update the ai scores to display in the UI
        for key in scores:
            self.ai_scores[key] = scores[key]
>>>>>>> upstream/main

    def increase_input(self):
        """
        Increments the input counter and updates line parameters periodically.
        """
        self.num_input +=1
        if self.num_input == 99:
            self.num_input = 0
        if self.num_input % 5 == 0:
            self.line_options["pattern_start"] += 5
            if self.line_options["pattern_start"] > 100:
                self.line_options["pattern_start"] = 1
  
    def reset(self):
        """
        Resets the input counter and accumulated chat.
        at the moment not called anywhere
        """
        self.num_input = 0
        self.accumulated_chat = ""

    def add_text(self, user_text, ai_text):
        """
        Adds user and AI text to the accumulated chat and user text, truncating if necessary.

        Args:
            user_text (str): The user's input text.
            ai_text (str): The AI's response text.
        """
        self.accumulated_chat += " " + user_text + " " + ai_text
        if len(self.accumulated_chat) > 500: ## Limit the text to 500 characters about 70 words
            self.accumulated_chat = self.accumulated_chat[-800:] 
            print("Text chat too long, truncating...")
        self.accumulated_user_text += " " + user_text
        if len(self.accumulated_user_text) > 200: ## Limit the text to 200 characters about 20 words
            self.accumulated_user_text = self.accumulated_user_text[-300:] 
            print("Text user too long, truncating...")

#helper functions
    @staticmethod
    def map_parameter_to_range(value, min_value, max_value, input_min, input_max):
        """
        Maps a value from one range to another.

        Args:
            value (float): The value to map.
            min_value (float): The minimum of the output range.
            max_value (float): The maximum of the output range.
            input_min (float): The minimum of the input range.
            input_max (float): The maximum of the input range.

        Returns:
            float: The mapped value.

        Raises:
            ValueError: If input or output ranges are invalid.
        """
        # Ensure the input range is valid
        if input_min >= input_max:
            raise ValueError("Input min must be less than input max")
        
        # Ensure the output range is valid
        if min_value >= max_value:
            raise ValueError("Output min must be less than output max")
        
        # Normalize the value to a 0-1 range based on the input range
        normalized_value = (value - input_min) / (input_max - input_min)
        
        # Map the normalized value to the output range
        mapped_value = min_value + normalized_value * (max_value - min_value)
        
        return mapped_value
    