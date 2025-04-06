import joblib
import numpy as np
import math
from skimage.io import imread
import librosa
import os
from telegram_bot.handlers import openai_text_classification, openai_text_embedding, openai_emotional_score

class ParametersHandler():
    def __init__(self, pattern):
        self.pattern = pattern
        self.accumulated_text = ""
        self.num_input = 0
        self.shape = "none"
        self.diameter = (0,0)
        self.growth_direction = (0, 0),
        self.rotation = 0
        self.bugs = 0
        self.pattern_height = 4
        self.pattern_width = 4
        self.pattern_spacing = 5
        self.inactive = False
        self.feature_vector = []

    def set_diameter(self, input_type, input):
        if input_type == "text":
            words = input.split(" ")
            #Word Density (Words per character count)
            word_density = len(words) / len(input) if len(input) > 0 else 0
            # Map the length of the input to a range between 15 and 60
            input_length = len(input)
            input_min = 1  # Minimum possible length of the input
            input_max = 300  # Maximum possible length of the input (adjust as needed)
            min_range = 50
            max_range = 100
            mapped_length = min_range + ((input_length - input_min) / (input_max - input_min)) * (max_range - min_range)
            mapped_length = max(min(mapped_length, max_range), min_range)
            self.diameter = (mapped_length, word_density * 230)
        if input_type == "image":
            img = imread(input, as_gray=True)
            # Calculate the average brightness (pixel intensity ranges from 0 to 1)
            avg_brightness = np.mean(img)
            median_brightness = np.median(img)
            # Map the average brightness to a value between 10 and 100
            self.diameter = (40 + 70 * avg_brightness, 40 + 70 * median_brightness)
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
     ai_classification = openai_text_classification(self.accumulated_text)
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
    
    def set_feature_vector(self, user_msg):
        # Convert the text to a vector using OpenAI's text embedding model
        self.feature_vector = openai_text_embedding(self.accumulated_text)
        self.feature_vector = [x *40 for x in self.feature_vector]  # Scale the vector to a range
        emotiaonal_score = openai_emotional_score(user_msg)
        try:
            emotiaonal_score = int(emotiaonal_score)
            print("emotional score: " + str(emotiaonal_score))
        except:
            emotiaonal_score = 1
            print("Error parsing emotional score, defaulting to 1")
        self.pattern_spacing = 7 - 2*emotiaonal_score # inverse emotional score

        
        

    def set_rotation(self, layer):
        if layer <= 0:
            return
        increase = self.num_input/layer
        if layer > 5:
            increase *= 20
        self.rotation += increase
  
    def set_new_epoch(self):
        self.num_input = 0
        self.accumulated_text = ""

    def add_text(self, text):
        self.accumulated_text += " "
        self.accumulated_text += text
        if len(self.accumulated_text) > 800: ## Limit the text to 1000 characters about 140 words
            self.accumulated_text = self.accumulated_text[-800:] 
            print("Text too long, truncating...")
        if len(text) < 2:
            self.inactive = True
    