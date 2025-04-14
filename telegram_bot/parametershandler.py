import joblib
import numpy as np
import math
from skimage.io import imread
import librosa
import os
from telegram_bot.handlers import openai_text_classification, openai_text_embedding, openai_scores

class ParametersHandler():
    def __init__(self, pattern):
        self.pattern = pattern
        self.accumulated_chat = ""
        self.accumulated_user_text = ""
        self.num_input = 0
        self.shape = "none"
        self.diameter = (70,70)
        self.growth_direction = (0, 0),
        self.rotation = 0
        self.bugs = 0
        self.pattern_height = 8
        self.pattern_width = 2
        self.pattern_spacing = 2
        self.inactive = False
        self.feature_vector = []

    def set_diameter(self, input_type, input):
        if input_type == "text":
            words = input.split(" ")
            #Word Density (Words per character count)
            word_density = len(words) / len(input) if len(input) > 0 else 0
            # Map the length of the input to a range between 15 and 60
            input_length = len(input)
            min_range = self.diameter[0] - 20
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
            min_range = self.diameter[0] - 20
            max_range = self.diameter[0] 
            mapped_avg_brightness = self.map_parameter_to_range(avg_brightness, min_range, max_range, 0, 1)
            min_range = self.diameter[1] - 20
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

    def get_pattern(self):
        return self.pattern
    
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
            "feature_vector": self.feature_vector,
        }
        self.bugs = 0
        return data
    
    def map_topic_to_pattern(self):
     ai_classification = openai_text_classification(self.accumulated_chat)
     # Parse the response to extract scores
     try:
        scores = eval(ai_classification)  # Convert string representation of dict to actual dict
        straight_score = float(scores.get("straight", 0))
        jagged_score = float(scores.get("jagged", 0))
        rectangular_score = float(scores.get("rectangular", 0))
        emotional_score = float(scores.get("emotional_intensity", 0))
        
        self.pattern_spacing = 3 + emotional_score*3
        # Return the pattern with the highest score
        if 0 >= jagged_score and 0 >= rectangular_score:
            self.pattern = "straight"
        elif rectangular_score > 0:
            self.pattern = "rectangular"
            self.pattern_height = 2 + jagged_score*3
            self.pattern_width = 2 + rectangular_score*4
        else:
            self.pattern = "jagged"
            self.pattern_width = 2 + rectangular_score*3
            self.pattern_height = 2 + jagged_score*3
        print(f"Scores: Straight: {straight_score}, Jagged: {jagged_score}, Rectangular: {rectangular_score}")
     except Exception as e:
        print(f"Error parsing AI response: {e}")
     #if "bug" in text:
      #   self.bugs += 1
     return self.pattern
    
    def set_pattern_parameters(self):
        # Convert the text to a vector using OpenAI's text embedding model
        self.feature_vector = openai_text_embedding(self.accumulated_chat)
        self.feature_vector = [x *self.pattern_height for x in self.feature_vector]  # Scale the vector to a range
        scores = openai_scores(self.accumulated_user_text)
        motivation_score = 0.5 # default if AI fails
        dynamics_score = 0.5
        complexity_score = 0.5

        try:
            scores = eval(scores)  # Convert string representation of dict to actual dict
            motivation_score = float(scores.get("motivational force", 0.5))
            dynamics_score = float(scores.get("social dynamics", 0.5))
            complexity_score = float(scores.get("cognitive complexity", 0.5))
        except Exception as e:
            print(f"Error parsing AI response: {e}")
        self.pattern_spacing = 6 - int(self.map_parameter_to_range(motivation_score, 0, 4, 0, 1))
        self.pattern_width = self.map_parameter_to_range(dynamics_score, -2, 4, 0, 1)
        #self.pattern_height = 4
        print(f"Scores: Motivation: {motivation_score}, Dynamics: {dynamics_score}, Complexity: {complexity_score}")

        
        

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
            print("Text too long, truncating...")
        self.accumulated_user_text += " " + user_text
        if len(self.accumulated_user_text) > 800: ## Limit the text to 1000 characters about 140 words
            self.accumulated_user_text = self.accumulated_user_text[-800:] 
            print("Text too long, truncating...")
    
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
    