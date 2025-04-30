import joblib
import numpy as np
import math
import json
from skimage.io import imread
import librosa
import os
from telegram_bot.handlers import openai_text_embedding, openai_text_scores, openai_image_scores

class ParametersHandler():
    def __init__(self, pattern):
        self.pattern = pattern
        self.accumulated_chat = ""
        self.accumulated_user_text = ""
        self.num_input = 0
        self.shape = "none"
        self.diameter = (60,60)
        self.growth_direction = (0, 0),
        self.rotation = 0
        self.bugs = 0
        self.pattern_height = 8
        self.pattern_width = 2
        self.pattern_spacing = 2
        self.inactive = False
        self.feature_vector = []
        self.num_center_points = 4

    def set_diameter(self, input_type, input):
        if input_type == "text":
            words = input.split(" ")
            #Word Density (Words per character count)
            word_density = len(words) / len(input) if len(input) > 0 else 0
            # Map the length of the input to a range between 15 and 60
            input_length = len(input)
            min_range = self.diameter[0] - 15
            max_range = self.diameter[0] 
            mapped_length = self.map_parameter_to_range(input_length, min_range, max_range, 1, 100)
            min_range = self.diameter[1] - 10
            max_range = self.diameter[1] 
            mapped_density = self.map_parameter_to_range(word_density, min_range, max_range, 0, 1)
            self.diameter = (mapped_length, mapped_density)
        if input_type == "image":
            img = imread(input, as_gray=True)
            # Calculate the average brightness (pixel intensity ranges from 0 to 1)
            avg_brightness = np.mean(img)
            median_brightness = np.median(img)
            min_range = self.diameter[0] - 15
            max_range = self.diameter[0] 
            mapped_avg_brightness = self.map_parameter_to_range(avg_brightness, min_range, max_range, 0, 1)
            min_range = self.diameter[1] - 15
            max_range = self.diameter[1] 
            mapped_median_brightness = self.map_parameter_to_range(median_brightness, min_range, max_range, 0, 1)
            self.diameter = (mapped_avg_brightness, mapped_median_brightness)
        if input_type == "voice":
            input_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), input)
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"File not found: {input_path}")
            
            y, sr = librosa.load(input_path, sr=None)
            rms = librosa.feature.rms(y=y) # Root Mean Square Energy loudness of the audio
            print("audio loudness: " + str(rms.mean()))
            self.diameter = (rms.mean() * 800, 30)

    def set_growth_direction(self, location):
        latiude = location["latitude"]
        longitude = location["longitude"]
        ref_lat = 47.390846
        ref_lon = 8.511541
        self.growth_direction = ((longitude - ref_lon) * 200, (latiude - ref_lat)*200)
    
    def get_parameters(self):
        data = {
            "shape": self.shape,
            "diameter": self.diameter,
            "growth_direction": self.growth_direction,
            "pattern": self.pattern,
            "rotation": self.rotation,
            "bugs": self.bugs,
            "pattern_height": self.pattern_height,
            "pattern_width": self.pattern_width,
            "pattern_spacing": self.pattern_spacing,
            "inactive": self.inactive,
            #"feature_vector": self.feature_vector,
            "center_points": self.num_center_points,
        }
        self.bugs = 0
        return data
        
    
    def set_pattern_parameters(self, user_text, image_url = None):
        # Convert the text to a vector using OpenAI's text embedding model
        #self.feature_vector = openai_text_embedding(self.accumulated_chat)
        #self.feature_vector = [x *self.pattern_height for x in self.feature_vector]  # Scale the vector to a range
        if image_url != None:
            scores = openai_image_scores(image_url)
            coherence_score = 0.5
        else:
            scores, coherence_score = openai_text_scores(user_text, self.accumulated_chat)
        motivation_score = 0.5 # default if AI fails
        dynamics_score = 0.5
        complexity_score = 0.5
        # Debugging: Print raw AI response
        print(f"Raw AI response (repr): {repr(scores)}")

        # Default scores
        motivation_score = 0.5  # Default if AI fails
        dynamics_score = 0.5
        complexity_score = 0.5
    # Strip Markdown-style code block formatting if present
        if scores.startswith("```") and scores.endswith("```"):
            scores = scores.strip("```").strip()
            # Remove the "json" label if it exists
            if scores.startswith("json"):
                scores = scores[4:].strip()

        # Strip whitespace and validate JSON format
        scores = scores.strip()
        if not scores.startswith("{") or not scores.endswith("}"):
            print("Error: AI response is not valid JSON.")
            
        try:
            scores = json.loads(scores)  # Parse the JSON string into a Python dictionary
            motivation_score = float(scores.get("motivational force", 0.5))
            dynamics_score = float(scores.get("social dynamics", 0.5))
            complexity_score = float(scores.get("complexity", 0.5))
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")
        max_spacing = 7 #480 // max(self.diameter[0], self.diameter[1]) 
        self.pattern_spacing = max_spacing - int(self.map_parameter_to_range(motivation_score, 0, 6, 0, 1))
        self.pattern_width = self.map_parameter_to_range(dynamics_score, -4, 4, 0, 1)
        # Set number of center points based on the complexity score
        num_center_points = int(self.map_parameter_to_range(complexity_score, 1, 4, 0, 1))
        if (self.shape == "none" or (self.shape == "circle" and image_url == None) or (self.shape == "rectangle" and image_url != None)):
            self.num_center_points = num_center_points
        # set pattern to straight line if the coherence score is low    
        if coherence_score < 0.5:
            self.pattern_height = 0
        else:
            self.pattern_height = 8

        print(f"Scores: Motivation: {motivation_score}, Dynamics: {dynamics_score}, Complexity: {complexity_score}, Coherence: {coherence_score}")      

    def set_rotation(self, layer):
        if layer <= 0:
            return
        increase = self.num_input/layer
        if layer > 2:
            increase *= 15
        self.rotation += increase
  
    def set_new_epoch(self):
        self.num_input = 0
        self.accumulated_chat = ""

    def add_text(self, user_text, ai_text):
        self.accumulated_chat += " " + user_text + " " + ai_text
        if len(self.accumulated_chat) > 800: ## Limit the text to 1000 characters about 140 words
            self.accumulated_chat = self.accumulated_chat[-800:] 
            print("Text chat too long, truncating...")
        self.accumulated_user_text += " " + user_text
        if len(self.accumulated_user_text) > 300: ## Limit the text to 1000 characters about 140 words
            self.accumulated_user_text = self.accumulated_user_text[-300:] 
            print("Text user too long, truncating...")
    
    def handle_inactivity(self, activity):
        if activity > 0:
            self.inactive = False
        else:
            self.inactive = True

    @staticmethod
    def map_parameter_to_range(value, min_value, max_value, input_min, input_max):
        """
        Maps a value from one range to another.
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
    