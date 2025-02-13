import joblib
import numpy as np
import math

class ParametersHandler():
    def __init__(self, pattern):
        self.pattern = pattern
        self.accumulated_text = ""
        self.num_input = 0
        self.count_input = 0
        self.epoch_height = 0
        self.start_layer = 0
        self.density = 4

    def get_pattern(self):
        return self.pattern
    
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
         self.pattern = "loop"
     elif topic_nr == 9:
         self.pattern = "cross_stitch"
     elif topic_nr == 10:
         self.pattern = "wave"
     else:
         self.pattern = "straight"
         
     return topic_nr, self.pattern

    def get_layer_rotation(self, layer_heigth, current_layer):
        if self.num_input == 0:
            return 0
        total_layers = math.ceil(self.epoch_height / layer_heigth)
        mod = math.ceil(total_layers / self.num_input)
        layer = current_layer - self.start_layer
        if layer % mod == 0:
            return 1
        else:
            return 0
  
    def set_new_epoch(self, height, layer):
        self.epoch_height = height
        self.start_layer = layer
        self.num_input = self.count_input
        self.count_input = 0
        self.accumulated_text = ""

    def add_text(self, text):
        self.accumulated_text += " "
        self.accumulated_text += text
    