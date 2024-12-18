from google.cloud import storage
import json

#bucket_name = 'anakena-2024'
bucket_name = 'test-bucket-nativa'

def create_lot(lot_name='default_lot'):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    lot_folder = f'{lot_name}'
    blob = bucket.blob(lot_folder)
    blob.upload_from_string('')
    return lot_folder

def save_data_to_lot(lot_name, name, data, data_type):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    lot_folder = create_lot(lot_name)
    object_name = f'{lot_folder}{name}'

    if data_type == 'image':
        blob = bucket.blob(object_name)
        blob.upload_from_filename(data)
    elif data_type == 'json':
        blob = bucket.blob(object_name)
        blob.upload_from_string(json.dumps(data))
    elif data_type == 'text':
        blob = bucket.blob(object_name)
        blob.upload_from_string(data)

    object_url = f'https://storage.cloud.google.com/{bucket_name}/{object_name}'

    return object_url