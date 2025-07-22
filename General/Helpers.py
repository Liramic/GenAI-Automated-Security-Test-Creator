import re
import json2html
import json
import os
from base64 import b64decode, b64encode
from General.JobClasses import JobType

def list_to_html_list(list):
    html = "<ol>"
    for item in list:
        html += f"<li>{item}</li>"
    html += "</ol>"
    return html

def html_to_python_list(html_string):
    # Regular expression to extract list items from HTML
    pattern = r'<li>(.*?)</li>'
    matches = re.findall(pattern, html_string, re.DOTALL)

    # Convert the matches to a Python list
    python_list = [match.strip() for match in matches]

    return python_list

def is_html_list_response(response):
    return "<li>" in response

if __name__ == "__main__":
    # Test the function
    python_list = ["item1", "item2", "item3"]
    html_string = list_to_html_list(python_list)
    print(html_string)
    print(html_to_python_list(html_string))
    new_list = "<ol><li>Identify the framework the component is using.</li><li>Check if this particular framework provides automatic binding of variables.</li><li>Verify if it is disabled or restricted.</li></ol>"
    print(html_to_python_list(new_list))


def save_as_html(json_data, path, filename_without_ext):
    if not os.path.exists(path):
        os.makedirs(path)
    json_data = json.dumps(json_data)
    with open(os.path.join(path, filename_without_ext) + ".html", 'w', encoding="utf-8") as outfile:
        outfile.write(json2html.json2html.convert(json=json_data))


def save_dict_as_html(dictionary, path, filename_without_ext):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename_without_ext) + ".html", 'w', encoding="utf-8") as outfile:
        outfile.write(json2html.json2html.convert(json=dictionary))

def save_dict_as_json(dictionary, path, filename_without_ext):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename_without_ext) + ".json", 'w', encoding="utf-8") as outfile:
        json.dump(dictionary, outfile, indent=4)

def load_dict_from_json(path):
    with open(path, 'r', encoding="utf-8") as infile:
        return json.load(infile)


def base64_decode(string):
    return b64decode(string).decode("utf-8")

def base64_encode(string: str):
    return b64encode(string.encode("utf-8")).decode("utf-8")

def base64_encode(byte_arr : bytes):
    return b64encode(byte_arr).decode("utf-8")

def get_output_folder(product_id, job_type = JobType.CREATE_TEST):
    folder = os.path.join("output_february_25", product_id)
    if not os.path.exists(folder):
        os.makedirs(folder)
    if job_type != "":
        folder = os.path.join(folder, job_type)
        if not os.path.exists(folder):
            os.makedirs(folder)
    return folder

def to_valid_windows_folder_name(name):
    """
    Converts a string into a valid Windows folder name by replacing invalid characters with an underscore (_).

    Parameters:
    name (str): The input folder name.

    Returns:
    str: The sanitized folder name.
    """
    # Define invalid characters for Windows folder names
    invalid_chars = r'[<>:"/\\|?*]'

    # Replace invalid characters with an underscore
    valid_name = re.sub(invalid_chars, '_', name)

    # Trim leading and trailing whitespace
    valid_name = valid_name.strip()

    # Ensure the name is not reserved
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    
    if valid_name.upper() in reserved_names:
        valid_name = f"_{valid_name}"

    # Ensure the name is not empty after sanitization
    if not valid_name:
        valid_name = "_"

    return valid_name

def normalize_newlines(input_string):
    """
    Removes multiple consecutive newline characters (\n, \r, \r\n)
    and any whitespace (including spaces) between them, replacing them with a single newline (\n).

    :param input_string: The input string to process.
    :return: A string with consecutive newlines (and spaces) replaced by a single newline.
    """
    # Normalize all newline variations to \n
    input_string = re.sub(r'\r\n|\r', '\n', input_string)
    # Replace multiple \n and any surrounding whitespace with a single \n
    return re.sub(r'[ \t]*\n[ \t\n]*', '\n', input_string.strip())

def remove_html_tags(text):
    """Remove html tags from a string"""
    if ( text == None or text == ""):
        return ""
    clean = re.compile('<.*?>')
    return normalize_newlines(re.sub(clean, '', text))