classes_dict = {'INSHELL': 'in-shell',
                'KERNEL': 'kernel'}

def str_to_dict(text):
    data_dict = {}
    for pair in text.split(','):
        key, value = pair.split(':', 1)
        data_dict[key.strip()] = value.strip()

    return data_dict


