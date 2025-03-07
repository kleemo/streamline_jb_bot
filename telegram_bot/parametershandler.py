import joblib
import numpy as np
import math
from skimage.io import imread
import librosa
import os

class ParametersHandler():
    def __init__(self, pattern):
        self.pattern = pattern
        self.accumulated_text = ""
        self.num_input = 0
        self.shape = "none"
        self.diameter = (0,0)
        self.growth_direction = (0, 0),
        self.rotation = 0

    def set_diameter(self, input_type, input):
        if input_type == "text":
            words = input.split(" ")
            #Word Density (Words per character count)
            word_density = len(words) / len(input) if len(input) > 0 else 0
            # Map the length of the input to a range between 15 and 60
            input_length = len(input)
            input_min = 1  # Minimum possible length of the input
            input_max = 400  # Maximum possible length of the input (adjust as needed)
            min_range = 15
            max_range = 65
            mapped_length = min_range + ((input_length - input_min) / (input_max - input_min)) * (max_range - min_range)
            mapped_length = max(min(mapped_length, max_range), min_range)
            self.diameter = (mapped_length, word_density * 160)
        if input_type == "image":
            img = imread(input, as_gray=True)
            # Calculate the average brightness (pixel intensity ranges from 0 to 1)
            avg_brightness = np.mean(img)
            median_brightness = np.median(img)
            # Map the average brightness to a value between 10 and 100
            self.diameter = (10 + 90 * avg_brightness, 10 + 90 * median_brightness)
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
            "rotation": self.rotation
        }
        return data
    
    def map_topic_to_pattern(self):
     vecotrizer = joblib.load("models\Text_vectorizer.pkl")
     text = vecotrizer.transform([self.accumulated_text])
     topic_extractor = joblib.load("models\Topic_extractor.pkl")
     topic_list = topic_extractor.transform(text)[0]
     topic_nr = np.argmax(topic_list) + 1

     if topic_nr == 4:
         self.pattern = "jagged"
     elif topic_nr == 5:
         self.pattern = "rectangle"
     elif topic_nr == 8:
         self.pattern = "straight"
     elif topic_nr == 9:
         self.pattern = "straight"
     elif topic_nr == 10:
         self.pattern = "straight"
     else:
         self.pattern = "straight"
         
     return topic_nr, self.pattern

    def set_rotation(self, layer):
        if layer <= 0:
            return
        increase = self.num_input/layer
        if layer > 5:
            increase *= 10
        self.rotation += increase
  
    def set_new_epoch(self):
        self.num_input = 0
        self.accumulated_text = ""

    def add_text(self, text):
        self.accumulated_text += " "
        self.accumulated_text += text
    