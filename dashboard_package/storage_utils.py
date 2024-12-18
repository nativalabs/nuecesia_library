import io
import json
from google.cloud import storage

bucket_name = 'test-bucket-nativa'
credentials_path = "auth-key-gabriel-nativa.json"
storage_client = storage.Client.from_service_account_json(credentials_path)

def create_lot(lot_name='default_lot'):
    bucket = storage_client.get_bucket(bucket_name)
    lot_folder = f'{lot_name}'
    blob = bucket.blob(lot_folder)
    blob.upload_from_string('')
    return lot_folder

def save_data_to_lot(lot_name, name, data, data_type):
    bucket = storage_client.get_bucket(bucket_name)
    lot_folder = create_lot(lot_name)
    object_name = f'{lot_folder}{name}'

    if data_type == 'image':
        buffer = io.BytesIO()
        data.save(buffer, format="PNG")
        blob = bucket.blob(object_name)
        blob.upload_from_string(buffer.getvalue())
    elif data_type == 'json':
        blob = bucket.blob(object_name)
        blob.upload_from_string(json.dumps(data))
    elif data_type == 'text':
        blob = bucket.blob(object_name)
        blob.upload_from_string(data)
    elif data_type == 'pdf':
        blob = bucket.blob(object_name)
        blob.upload_from_string(data, content_type='application/pdf')

    object_url = f'https://storage.cloud.google.com/{bucket_name}/{object_name}'

    return object_url