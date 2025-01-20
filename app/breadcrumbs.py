import os
import tiktoken
from streamlit_tree_select import tree_select
from datetime import datetime
import traceback
import streamlit as st
from pathlib import Path
import base64

#Setting up the token encoder
encoding = tiktoken.get_encoding("cl100k_base")
excluded_directories = ['.', '__', 'venv', 'node_modules', 'dist', 'build', 'target', 'out', 'cache']


def get_icon_path(extension):
    icon_map = {
        'py': 'file_type_python.svg',
    }
    icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
    icon_name = icon_map.get(extension.lower(), 'default_file.svg')
    icon_path = os.path.join(icons_dir, icon_name)
    if os.path.exists(icon_path):
        return icon_path
    default_icon_path = os.path.join(icons_dir, 'default_file.svg')
    return default_icon_path if os.path.exists(default_icon_path) else None

def generate_data_uri(file_path):
    """
    Generates a Data URI for an SVG file.
    """
    try:
        mime_type = 'image/svg+xml'
        with open(file_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        print(f"Error generating data URI: {e}")
        return None


def create_file_label(item, icon_uri):
    if icon_uri:
        # Create HTML with the SVG image
        label = (
            '<span class="file-item">'
            f'<img src="{icon_uri}" '
            'style="width:20px;height:20px;vertical-align:middle;margin-right:5px"/>'
            f' {item}'
            '</span>'
        )
    else:
        label = f"📄 {item}"
    return label


def generate_folder_tree(root_folder, utils):
    tree = []
    try:
        root_folder = os.path.abspath(root_folder)
        for item in sorted(os.listdir(root_folder)):
            if item.startswith('.') or item in excluded_directories:
                continue
                
            path = os.path.join(root_folder, item)
            
            if os.path.isdir(path):
                children = generate_folder_tree(path, utils)
                if children:
                    node = {
                        "label": item,
                        "value": path,
                        "children": children
                    }
                    tree.append(node)
            else:
                icon_data = utils.get_file_icon(path)
                if icon_data:
                    label = f'<span><img src="{icon_data}"/>{item}</span>'
                else:
                    label = f"📄 {item}"
                    
                node = {
                    "label": label,
                    "value": path
                }
                tree.append(node)
                
        return tree
    except Exception as e:
        print(f"Error generating tree: {str(e)}")
        return []
    
def num_tokens_from_string(string: str) -> int:
    """
    Calculates the number of tokens in a text string.

    Args:
    string (str): Text to process.

    Returns:
    int: Number of tokens in the text.
    """
    return len(encoding.encode(string))
