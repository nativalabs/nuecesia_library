from PIL import Image, ImageOps
import numpy as np
import requests
from google.cloud import storage

class_names = open("labels.txt", "r").readlines()

def prepare_image_for_model(filepath):
    image_data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    image = Image.open(filepath).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    image_data[0] = normalized_image_array
    return image_data

github_model_url = 'https://github.com/gabriel-nativa/yield-humidity-model/raw/main/keras_model_yield_humidity_counts.h5'
def download_model_from_github(model_url, model_name):    
    destination_path = f"/tmp/{model_name}"
    response = requests.get(model_url)

    with open(destination_path, 'wb') as file:
        file.write(response.content)

def download_model_from_gcs(bucket_name, model_name, destination_path):    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(model_name)
    blob.download_to_filename(destination_path)
