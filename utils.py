import pandas as pd
from google.cloud import storage
import json
import io
from PIL import Image
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st
import datetime
from matplotlib import patheffects
from sqlalchemy import text

credentials_path = "auth-key-gabriel-nativa.json"
storage_client = storage.Client.from_service_account_json(credentials_path)

database = "nueces_vitakai"
bucket_name = 'vitakai-2024'
#bucket_name = 'test-bucket-nativa'

sql_connection = st.session_state["vk_connection"]

@st.cache_data(ttl=60)
def fetch_data(query,_connection):
    data = pd.read_sql(query,_connection)
    return data

def create_lot(lot_name='default_lot'):
    bucket = storage_client.get_bucket(bucket_name)
    lot_folder = f'{lot_name}'
    blob = bucket.blob(lot_folder)
    blob.upload_from_string('')
    return lot_folder

def sort_predictions(predictions_json):
    data = predictions_json['predictions']

    y_threshold = sum(e['height'] for e in data) / len(data)
    x_threshold = sum(e['width'] for e in data) / len(data)

    for element in data:
        element['center_y'] = element['y'] - element['height'] / 2
        
    rows = {}
    for element in data:
        row_key = int(element['center_y'] // y_threshold)
        if row_key not in rows:
            rows[row_key] = []
        rows[row_key].append(element)

    for row_key, row_elements in rows.items():
        mean_y = sum(e['center_y'] for e in row_elements) / len(row_elements)
        for e in row_elements:
            e['new_y'] = mean_y
    
    min_x = min(e['x'] for e in data)
    max_x = max(e['x'] for e in data)
    
    num_columns = round((max_x - min_x) / x_threshold)
    sorted_data = sorted(data, key=lambda e: (e['new_y'] * num_columns) + (e['x'] - (e['width']/2)))
    
    sorted_predictions = {'time': predictions_json['time'], 'image': predictions_json['image'], 'predictions': sorted_data}
    return sorted_predictions

def remove_points(data):
    for prediction in data.get("predictions", []):
        if "points" in prediction:
            del prediction["points"]
    return data

def update_sql_table(connection, table_name, edited_data, original_data, identifier_column, value_column):
    indexes_edited = original_data.compare(edited_data).index
    update_queries = []
    for index in indexes_edited:
        ID_value = edited_data.loc[index, identifier_column]
        new_value = edited_data.loc[index, value_column]
        
        update_query = f"""UPDATE {table_name} SET {value_column} = '{new_value}' WHERE {identifier_column} = '{ID_value}'"""
        update_queries.append(update_query)

    if update_queries:
        try:
            with connection.connect() as conn:
                with conn.begin():
                    for query in update_queries:
                        conn.execute(text(query))
            return True
        except Exception as e:
            print(e)
            return False


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

from datetime import datetime, timedelta

def convert_utc_to_chilean_time(utc_timestamp):    
    utc_timestamp = str(utc_timestamp)
    # Parse the UTC timestamp
    utc_time = datetime.strptime(utc_timestamp, "%Y-%m-%d %H:%M:%S")
    # Subtract 4 hours to UTC time for Chilean time
    chilean_time = utc_time - timedelta(hours=4)
    # Format the Chilean time
    formatted_time = chilean_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


@st.cache_data(show_spinner='Cargando imagen')
def download_image_from_gcs(blob_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    image_data = blob.download_as_string()
    image = Image.open(io.BytesIO(image_data))
    
    return image

@st.cache_data(show_spinner='Generando imágen')
def plot_patches(_image, data, plot_color_dict, counts_dict, translate_dict):
    fig, ax = plt.subplots()
    ax.imshow(_image)
    ax.axis('off')
    used_classes = set()
    
    for i in range(len(data['predictions'])):
        color = plot_color_dict[data['predictions'][i]['class']]
        used_classes.add(data['predictions'][i]['class']) 
        rect = patches.Rectangle((data['predictions'][i]['x'] - 0.5 * data['predictions'][i]['width'],
                                  data['predictions'][i]['y'] - 0.5 * data['predictions'][i]['height']),
                                  data['predictions'][i]['width'], data['predictions'][i]['height'],
                                  linewidth=1, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
    
    markers = [plt.Line2D([0, 0], [0, 0], color=plot_color_dict[class_name], marker='o', linestyle='') for class_name in used_classes]
    labels = [translate_dict[class_name]+': '+str(counts_dict[class_name]) for class_name in used_classes]
    
    plt.legend(markers, labels, numpoints=1, ncol=5, prop={'size': 4},loc='upper right', bbox_to_anchor=(1, 1))
    
    buf = io.BytesIO()
    plt.savefig(buf, format='jpg',bbox_inches='tight',dpi = 1000, pad_inches=0)
    buf.seek(0)

    pil_image = Image.open(buf)
    plt.close(fig)

    return pil_image

def get_class_counts(json_data, inspection_dict):
    results = json_data
    counts = Counter(tok['class'] for tok in results['predictions'])
    count_dict = dict(counts)

    for key in inspection_dict.keys():
        if key not in count_dict:
            count_dict.update({key: 0})
            
    return count_dict

@st.cache_data(show_spinner='Generando índices')
def plot_indexes(_image, data, plot_color_dict, translate_dict, y_filter='new_y'):
    fig, ax = plt.subplots()
    ax.imshow(_image)
    ax.axis('off')
    used_classes = set()
   
    for i in range(len(data['predictions'])):
        color = plot_color_dict[data['predictions'][i]['class']]
        used_classes.add(data['predictions'][i]['class']) 
        
        text = ax.text(data['predictions'][i]['x']-20, data['predictions'][i][y_filter]+20,
                i+1, fontsize=6.5, color=color)
        text.set_path_effects([patheffects.Stroke(linewidth=0.5, foreground='black'), patheffects.Normal()])
    
    markers = [plt.Line2D([0, 0], [0, 0], color=plot_color_dict[class_name], marker='o', linestyle='') for class_name in used_classes]
    labels = [translate_dict[class_name] for class_name in used_classes]
   
    plt.legend(markers, labels, numpoints=1, ncol=5, prop={'size': 4},loc='upper right', bbox_to_anchor=(1, 1))

    buf = io.BytesIO()
    plt.savefig(buf, format='jpg',bbox_inches='tight',dpi = 1000, pad_inches=0)
    buf.seek(0)

    pil_image = Image.open(buf)
    plt.close(fig)

    return pil_image

def add_d0_to_counts(data, counts):
    defects_inside_inshell = []
    for i in range(len(data['predictions'])):
        if data['predictions'][i]['class'] != 'w-in-shell':
            centroid = {'x': data['predictions'][i]['x'],'y': data['predictions'][i]['y']}
            matches = []
            for j in range(len(data['predictions'])):
                obj = data['predictions'][j]
                if obj['class'] == 'w-in-shell' and is_centroid_inside_object(centroid,obj):
                    if obj not in matches:
                        matches.append(obj)
            if matches:
                defects_inside_inshell.append(matches)
    
    counts['d-0'] = counts['w-in-shell'] - len(defects_inside_inshell)
    return counts

def process_ext_defects(data):
    unique_classes = []
    for i in range(len(data['predictions'])):
        obj = data['predictions'][i]
        if obj['class'] != 'w-in-shell':
            unique_classes.append(obj)
        elif obj['class'] == 'w-in-shell':
            matches = []
            for j in range(len(data['predictions'])):
                if data['predictions'][j]['class'] != 'w-in-shell':
                    centroid = {'x': data['predictions'][j]['x'],'y': data['predictions'][j]['y']}
                    if is_centroid_inside_object(centroid,obj):
                        if data['predictions'][j] not in unique_classes:
                            matches.append(data['predictions'][j])
                
            if matches == []:
                unique_classes.append(obj)

    return {'time': data['time'], 'image': data['image'], 'predictions': unique_classes}

def parse_predictions(data, parse=True):
    if not parse:
        return data
    
    filtered_data = []
    for i in range(len(data['predictions'])):
        centroid = {'x': data['predictions'][i]['x'],'y': data['predictions'][i]['y']}
        matches = []
        matches.append(data['predictions'][i])
        for j in range(len(data['predictions'])):
            obj = data['predictions'][j]
            if i!=j and is_centroid_inside_object(centroid,obj):
                matches.append(obj)
        
        if max(matches, key=lambda x:x['confidence']) not in filtered_data:
            filtered_data.append(max(matches, key=lambda x:x['confidence']))
    
    return {'time': data['time'], 'image': data['image'], 'predictions': filtered_data}

def is_centroid_inside_object(centroid, obj):
    return (obj['x'] - 0.5*obj['width'] <= centroid['x'] <= obj['x'] + 0.5*obj['width']) and (obj['y'] - 0.5*obj['height'] <= centroid['y'] <= obj['y'] + 0.5*obj['height'])
