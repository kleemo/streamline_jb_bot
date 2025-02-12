import joblib
import numpy as np

class ParametersHandler():
    def __init__(self, pattern):
        self.pattern = pattern

    def get_pattern(self):
        return self.pattern
    
    def map_topic_to_pattern(self, text):
     vecotrizer = joblib.load("models\Text_vectorizer.pkl")
     text = vecotrizer.transform([text])
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
         
     return topic_nr

    