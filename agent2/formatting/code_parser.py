from typing import List
from agent2.element import Element
from agent2.formatting.parsers.parse_python import parse_python_elements

def parse_code(code : str, extension) -> List:
    if extension == "py":
        return parse_python_elements(code)
    else:
        return [Element("Content", code, "", 0, None, [])]