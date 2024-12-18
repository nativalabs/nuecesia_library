from collections import Counter

def get_class_counts(json_data, inspection_dict):
    results = json_data
    counts = Counter(tok['class'] for tok in results['predictions'])
    count_dict = dict(counts)

    for key in inspection_dict.keys():
        if key not in count_dict:
            count_dict.update({key: 0})
            
    return count_dict

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

def parse_predictions(data):
    predictions = data['predictions']
    filtered_data = []

    for current in predictions:
        centroid = {'x': current['x'], 'y': current['y']}
        
        matches = [obj for obj in predictions if is_centroid_inside_object(centroid, obj)]
        matches.append(current)
        
        best_match = max(matches, key=lambda x: x['confidence'])
        
        if best_match not in filtered_data:
            filtered_data.append(best_match)

    return {'time': data['time'], 'image': data['image'], 'predictions': filtered_data}

def is_centroid_inside_object(centroid, obj):
    return (obj['x'] - 0.5*obj['width'] <= centroid['x'] <= obj['x'] + 0.5*obj['width']) and (obj['y'] - 0.5*obj['height'] <= centroid['y'] <= obj['y'] + 0.5*obj['height'])


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