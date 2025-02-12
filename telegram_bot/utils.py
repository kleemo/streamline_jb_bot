from skimage.io import imread
from skimage.transform import resize
import joblib
import numpy as np

# this file should be replaced by the classes in the same folder
def image_encoder(image_url):
        img = imread(image_url, as_gray=True)
        print("imgage loaded ")
        # Resize the image
        original_height, original_width = img.shape
        max_size = 64
        scaling_factor = max(max_size / original_height, max_size / original_width)
        new_height = int(original_height * scaling_factor)
        new_width = int(original_width * scaling_factor)
        img = resize(img, (new_height+1, new_width+1), anti_aliasing=True)
        img = img[0:64,0:64]
        print("imgage resized")
        print(img.shape)
        flatten_img = img.flatten()
        print(flatten_img.shape)
        if flatten_img.shape != (4096,):
            return "image wrong dimensions"
        
        new_data = [flatten_img]
        rbm = joblib.load("models\model_rbm_images.pkl")
        transformed_data = rbm.transform(new_data)
        print("data transformed")

        return transformed_data[0] #return image encoded with 10 variables

def map_brightness_to_value(image_url, min, max):
    img = imread(image_url, as_gray=True)
    # Calculate the average brightness (pixel intensity ranges from 0 to 1)
    avg_brightness = np.mean(img)
    # Map the average brightness to a value between min and max
    value = min + (max - min) * avg_brightness
    value = round(value)
    return value

def check_location(longitude):
    lon_ref = 8.32443 #reference longitude toni areal
    threshold = 0.007
    if abs(longitude - lon_ref) < threshold:
        return "center"
    if longitude < lon_ref:
        return "left" #west
    else:
        return "right" #east
    
def map_topic_to_pattern(text):
     vecotrizer = joblib.load("models\Text_vectorizer.pkl")
     text = vecotrizer.transform([text])
     topic_extractor = joblib.load("models\Topic_extractor.pkl")
     topic_list = topic_extractor.transform(text)[0]
     topic_nr = np.argmax(topic_list) + 1

     if topic_nr == 4:
         return "jagged", topic_nr
     elif topic_nr == 5:
         return "rectangle", topic_nr 
     elif topic_nr == 8:
         return "loop", topic_nr
     elif topic_nr == 9:
         return "cross_stitch", topic_nr
     elif topic_nr == 10:    
         return "wave", topic_nr
     else:
         return "straight", topic_nr

 
