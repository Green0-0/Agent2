from typing import List
from agent2.element import Element
from agent2.file import File
import requests
import time
import os
import re

from typing import List

def extract_all_code_blocks(text: str) -> List[str]:
    code_blocks = []
    parts = text.split('```')
    for i in range(1, len(parts), 2):
        cb_content = parts[i]
        split_content = cb_content.split('\n', 1)
        if len(split_content) > 1:
            code = split_content[1]
        else:
            code = ''
        code_blocks.append(code)
    return code_blocks

def get_overlaps(line_start: int, line_end: int, file: File) -> List[Element]:
    overlapping_elements = []
    
    def collect_overlapping(elements: List[Element]):
        for element in elements:
            content_lines = element.content.split('\n')
            element_line_count = len(content_lines)
            e_start = element.line_start
            e_end = e_start + element_line_count - 1
            if e_start <= line_end and e_end >= line_start:
                overlapping_elements.append(element)
                collect_overlapping(element.elements)
    
    collect_overlapping(file.elements)
    
    exception_candidates = []
    for elem in overlapping_elements:
        if not elem.elements:
            content_lines = elem.content.split('\n')
            e_line_count = len(content_lines)
            e_start = elem.line_start
            e_end = e_start + e_line_count - 1
            overlap_start = max(e_start, line_start)
            overlap_end = min(e_end, line_end)
            if overlap_start > overlap_end:
                continue
            overlap_lines = overlap_end - overlap_start + 1
            if overlap_lines >= 4:
                pre_lines = max(0, line_start - e_start)
                post_lines = max(0, e_end - line_end)
                if pre_lines <= 2 and post_lines <= 2:
                    exception_candidates.append(elem)
    
    if exception_candidates:
        deepest = max(exception_candidates, key=lambda x: len(x.identifier.split('.')))
        return [deepest]
    else:
        return overlapping_elements
    
# Assume this function is implemented to interface with your LLM API
def get_completion(oai_messages, timeout_duration : int = 120, max_retries : int = 5, api_url : str = "https://api.mistral.ai/v1", api_key : str = os.environ.get("API_KEY"), model : str = "mistral-small-2501") -> str:  
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': f"{model}",
        'messages': oai_messages,
        'stream': False,
        'temperature': 0.3,
        'top_p': 0.95,
        'max_tokens': 2000,
        'stop': ['</s>', "<|im_end|>", "</tool_call>", "</tool_use>"]
    }
    
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.post(api_url + '/chat/completions', headers=headers, json=data, timeout=timeout_duration)
            response.raise_for_status()  # Raise an exception for bad status codes
            response = response.json()
            try: 
                response = response['choices'][0]['message']['content']
                return response
            except KeyError:
                print("Response does not have the expected format: ", response)
        except requests.Timeout:
            print(f"Request timed out, retrying ({retry_count}/{max_retries})...")
        except requests.RequestException as e:
            print(f"Error during request: {str(e)}")
            print(f"Retrying ({retry_count}/{max_retries})...")
        retry_count += 1
        time.sleep(10)
    
    raise requests.RequestException("Max retries exceeded")

def load_project_files(root_path="examples/astropy") -> List[File]:
    """Load all files recursively from the specified directory, skipping binary files."""
    project_files = []
    for root, _, files in os.walk(root_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                relative_path = os.path.relpath(file_path, root_path)
                project_files.append(File(relative_path.replace("\\", "/"), content))
            except (UnicodeDecodeError, IsADirectoryError):
                continue
    return project_files

def get_rating_keys(s):
    # Check uppercase terms in order of longest to shortest
    upper_terms = ['VERY_UNLIKELY', 'VERY_LIKELY', 'UNLIKELY', 'POSSIBLE', 'LIKELY']
    upper_pattern = re.compile('|'.join(upper_terms))
    upper_matches = upper_pattern.findall(s)
    
    if upper_matches:
        last_upper = upper_matches[-1]
        if last_upper == 'VERY_LIKELY':
            return 2
        elif last_upper == 'LIKELY':
            return 1
        elif last_upper == 'POSSIBLE':
            return 0
        elif last_upper == 'UNLIKELY':
            return -1
        elif last_upper == 'VERY_UNLIKELY':
            return -2
    
    # Check lowercase terms in order of longest to shortest
    lower_terms = [term.lower() for term in upper_terms]
    lower_pattern = re.compile('|'.join(lower_terms))
    lower_matches = lower_pattern.findall(s)
    
    if lower_matches:
        last_lower = lower_matches[-1]
        if last_lower == 'very_likely':
            return 2
        elif last_lower == 'likely':
            return 1
        elif last_lower == 'possible':
            return 0
        elif last_lower == 'unlikely':
            return -1
        elif last_lower == 'very_unlikely':
            return -2
    
    # If no terms found in either case
    return 0

def get_first_import_block(code):
    lines = code.split('\n')
    block_lines = []
    in_block = False
    open_parens = 0
    line_continuation = False

    for line in lines:
        stripped = line.strip()

        if not in_block:
            if stripped == '' or stripped.startswith('#'):
                continue
            elif 'import' in line:
                in_block = True
                block_lines.append(line)
                open_parens += line.count('(') - line.count(')')
                line_continuation = line.rstrip().endswith('\\')
        else:
            is_comment_or_empty = stripped == '' or stripped.startswith('#')
            if is_comment_or_empty:
                block_lines.append(line)
                continue

            if line_continuation or open_parens > 0:
                block_lines.append(line)
                open_parens += line.count('(') - line.count(')')
                line_continuation = line.rstrip().endswith('\\')
            else:
                if 'import' in line:
                    block_lines.append(line)
                    open_parens += line.count('(') - line.count(')')
                    line_continuation = line.rstrip().endswith('\\')
                else:
                    break

    return '\n'.join(block_lines)