import streamlit as st
import io
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import patheffects

@st.cache_data(show_spinner='Dibujando sobre la imágen...')
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

@st.cache_data(show_spinner='Dibujando sobre la imágen...')
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

@st.cache_data(show_spinner='Descargando imágen...')
def download_image_from_gcs(blob_name, storage_client, bucket_name='test-bucket-nativa'):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    image_data = blob.download_as_string()
    image = Image.open(io.BytesIO(image_data))
    
    return image