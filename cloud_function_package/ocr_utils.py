import os
from google.cloud import documentai
import re

project_id = "roboflowinferencev1"
processor_id = "278af8e1f138c7c2"
location = "us"
mime_type = "image/jpeg"

def process_document_sample(image_path):
    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(project_id, location, processor_id)

    with open(image_path, "rb") as image:
        image_content = image.read()

    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
        field_mask=None,
        process_options=None)

    result = client.process_document(request=request)
    document = result.document

    return document.text

re_patterns = {'LOTE': r'\s*LOTE:\s*(\d+)',
               'PROCESO': r'\bPROCESO:\s*(\w+)\b',
               'VARIEDAD': r'\bVARIEDAD:(SERR|CHANDLER|FRANQUETTE|HOWARD)\b',
               'PRODUCTOR': r'\bPRODUCTOR:\s*(.*)',
               'CALIBRE': r'\bCALIBRE:\s*(.*)',
               'ANALISTA': r'\bANALISTA:\s*(.*)'
               }

label_patterns = [r'\bHUM:\d{3}\b']

#fail_patterns = {'ERR': 'SERR', 'HANDLER': 'CHANDLER', 'OWARD': 'HOWARD'}
                
def perform_ocr(image_path):
    text = process_document_sample(image_path)
    print(text)
    temp_dict = {'LOTE': None,
               'PROCESO': None,
               'VARIEDAD': None,
               'PRODUCTOR': None,
               'CALIBRE': None,
               'ANALISTA': None,
               'OCR_LABEL': None
               }
    for keyword, pattern in re_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            # If the match is a tuple, select the non-None value
            for match in matches:
                if isinstance(match, tuple):
                    temp_dict.update({keyword: next(filter(None, match))})
                else:
                    temp_dict.update({keyword: match})
        else:
            pass

        if keyword == 'PRODUCTOR':
            lines = text.splitlines()
            captured_text = ''
            capturing = False
            
            for i, line in enumerate(lines):
                if 'PRODUCTOR:' in line:
                    match = re.search(pattern, line)
                    if match:
                        captured_text += match.group(1).strip()
                        capturing = True
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line:
                                captured_text += ' ' + next_line
                    break 
            temp_dict.update({keyword: captured_text.strip()})        

    for label_pattern in label_patterns:
        label_match = re.findall(label_pattern, text)
        if label_match:
            temp_dict.update({'OCR_LABEL': label_match[0]})
    
    return temp_dict