from PIL import Image
from collections import Counter
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class PredictionClass:
    def __init__(self, class_name, sql_name, color, translation):
        self.class_name = class_name #Roboflow class name
        self.sql_name = sql_name #SQL Table column name
        self.color = color #Plot color
        self.translation = translation #Translated name

    def __repr__(self):
        return f"PredictionClass({self.class_name}, {self.sql_name}, {self.color}, {self.translation})"
    
def remove_points(data):
    for prediction in data.get("predictions", []):
        if "points" in prediction:
            del prediction["points"]
    return data

def is_centroid_inside_object(centroid, obj, margin=0):
    """
    Checks if a centroid is inside the bounding box of an object.
    Expands the object's bounding box by a margin.
    """
    margin_width = obj['width'] * margin
    margin_height = obj['height'] * margin

    return (
        obj['x'] - 0.5 * obj['width'] - margin_width <= centroid['x'] <= obj['x'] + 0.5 * obj['width'] + margin_width
        and obj['y'] - 0.5 * obj['height'] - margin_height <= centroid['y'] <= obj['y'] + 0.5 * obj['height'] + margin_height
    )
    
def adjust_confidence(obj, classes):
    """
    Adjust the confidence value of the given object's class based on a provided list of classes.

    Parameters:
    - obj (dict): The object containing 'class' and 'confidence' keys.
    - classes (list): A list of class names. Confidence values will be assigned incrementally,
                      starting from 0.1 for the first class, 0.11 for the second, etc.

    Returns:
    - dict: The updated object with adjusted confidence.
    """
    
    class_confidences = {cls: 0.1 + 0.01 * i for i, cls in enumerate(classes)}

    if obj['class'] in class_confidences:
        obj['confidence'] = class_confidences[obj['class']]

    return obj

def parse_predictions(data, classes=None):
    """
    Parameters:
        data (dict): A dictionary containing 'predictions' (list of predicted objects), 
                    'time' (timestamp), and 'image' (image reference).
        classes (list): A list of class labels used for adjusting prediction confidence.

    Returns:
        dict: A dictionary containing 'time', 'image', and a filtered list of 'predictions'.
    """
    classes = classes or []

    predictions = [
        adjust_confidence(prediction, classes) for prediction in data['predictions']
    ]

    filtered_data = []
    seen_ids = set()

    for i, pred in enumerate(predictions):
        centroid = {'x': pred['x'], 'y': pred['y']}
        matches = [pred]

        matches.extend(
            other
            for j, other in enumerate(predictions)
            if i != j and is_centroid_inside_object(centroid, other)
        )

        highest_confidence_obj = None
        largest_obj = None
        for obj in matches:
            if highest_confidence_obj is None or obj['confidence'] > highest_confidence_obj['confidence']:
                highest_confidence_obj = obj
            if largest_obj is None or obj['width'] * obj['height'] > largest_obj['width'] * largest_obj['height']:
                largest_obj = obj

        if highest_confidence_obj is not None and largest_obj is not None:
            highest_confidence_obj.update({
                'x': largest_obj['x'],
                'y': largest_obj['y'],
                'width': largest_obj['width'],
                'height': largest_obj['height']
            })

        if id(highest_confidence_obj) not in seen_ids:
            filtered_data.append(highest_confidence_obj)
            seen_ids.add(id(highest_confidence_obj))

    return {'time': data['time'], 'image': data['image'], 'predictions': filtered_data}

def get_class_counts(results, inspection_classes):
    """
    Count occurrences of each class in the predictions and ensure all keys 
    in the inspection_dict are represented in the output with a count of zero if missing.

    Parameters:
    - results (dict): A dictionary containing predictions under the 'predictions' key.
                      Each prediction should be a dictionary with a 'class' key.
    - inspection_classes (PredictionClass list): A list of all expected classes.

    Returns:
    - dict: A dictionary with counts for each class.
    """
    counts = Counter(tok['class'] for tok in results.get('predictions', []))
    inspection_class_keys = [pc.class_name for pc in inspection_classes]
    
    return {key: counts.get(key, 0) for key in inspection_class_keys}

def plot_patches(image, data, prediction_classes):
    """
    Plots bounding boxes (patches) on an image based on prediction data.

    Parameters:
    - image (str or path-like): Path to the image file.
    - data (dict): Contains prediction data with keys 'x', 'y', 'width', 'height', and 'class'.
    - prediction_classes (list of PredictionClass): A list of PredictionClass objects.

    Returns:
    - fig: The matplotlib figure object containing the plotted image with bounding boxes.
    """
    
    class_info = {pc.class_name: pc for pc in prediction_classes}
    
    img = Image.open(image)
    fig, ax = plt.subplots()
    
    ax.imshow(img)
    ax.axis('off')
    
    used_classes = set()

    for prediction in data.get('predictions', []):
        class_name = prediction['class']
        if class_name not in class_info:
            continue
        
        pc = class_info[class_name]
        color = pc.color
        used_classes.add(class_name)
        
        x = prediction['x'] - 0.5 * prediction['width']
        y = prediction['y'] - 0.5 * prediction['height']
        rect = patches.Rectangle(
            (x, y), prediction['width'], prediction['height'],
            linewidth=1, edgecolor=color, facecolor='none'
        )
        ax.add_patch(rect)

    markers = [
        plt.Line2D([0], [0], color=class_info[class_name].color, marker='o', linestyle='', markersize=4) 
        for class_name in used_classes
    ]
    labels = [
        f"{class_info[class_name].translation}: {data['predictions'].count({'class': class_name})}" 
        for class_name in used_classes
    ]
    ax.legend(
        markers, labels, numpoints=1, ncol=3, prop={'size': 3.5},
        loc='upper right', bbox_to_anchor=(1, 1)
    )

    return fig

def replace_classes(json_data, class_mapping):
    """
    Replace class names in the 'predictions' of a JSON object based on a mapping.

    Parameters:
    - json_data (dict): A dictionary containing predictions under the 'predictions' key.
    - class_mapping (dict): A dictionary where keys are original class names and values are replacement class names.

    Returns:
    - dict: The updated JSON object with class names replaced as specified in class_mapping.
    """
    
    for prediction in json_data.get('predictions', []):
        class_label = prediction['class']
        if class_label in class_mapping:
            prediction['class'] = class_mapping[class_label]
    return json_data
