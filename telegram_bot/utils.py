from skimage.io import imread
from skimage.transform import resize
import joblib

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

def check_location(longitude):
    lon_ref = 8.32443 #reference longitude toni areal
    threshold = 0.007
    if abs(longitude - lon_ref) < threshold:
        return "center"
    if longitude < lon_ref:
        return "left" #west
    else:
        return "right" #east