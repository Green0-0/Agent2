from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List
from agent2.element import Element

# THIS WORKS

def parse_python_elements(code: str) -> List[Element]:
    parser = get_parser('python')
    code_bytes = code.encode('utf8')  # Encode once here
    tree = parser.parse(code_bytes)
    root_node = tree.root_node

    language = get_language('python')
    doc_str_pattern = """
        (module 
            . (comment)* 
            . (expression_statement (string)) @module_doc_str
        )
        
        (class_definition
            body: (block 
                . (expression_statement (string)) @class_doc_str
            )
        )
        
        (function_definition
            body: (block 
                . (expression_statement (string)) @function_doc_str
            )
        )
    """
    doc_str_query = language.query(doc_str_pattern)
    captures = doc_str_query.captures(root_node)

    element_to_docstring = {}
    for node, capture_name in captures:
        current_node = node
        element_node = None
        while current_node:
            if capture_name == 'module_doc_str' and current_node.type == 'module':
                element_node = current_node
                break
            elif capture_name == 'class_doc_str' and current_node.type == 'class_definition':
                element_node = current_node
                break
            elif capture_name == 'function_doc_str' and current_node.type == 'function_definition':
                element_node = current_node
                break
            current_node = current_node.parent
        if element_node is not None:
            # Use code_bytes here
            docstring = code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
            element_to_docstring[element_node] = docstring

    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        actual_node = node
        decorators = []
        
        if node.type == 'decorated_definition':
            decorators = [c for c in node.children if c.type == 'decorator']
            for child in node.children:
                if child.type in ['function_definition', 'class_definition']:
                    actual_node = child
                    break

        if actual_node.type not in ['function_definition', 'class_definition']:
            return None

        # Extract name from code_bytes
        name_node = next((c for c in actual_node.children if c.type == 'identifier'), None)
        if not name_node:
            return None
        name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
        identifier = f"{parent_identifier}.{name}" if parent_identifier else name

        line_start = actual_node.start_point[0]
        if decorators:
            line_start = min(d.start_point[0] for d in decorators)

        start_byte = decorators[0].start_byte if decorators else actual_node.start_byte
        end_byte = actual_node.end_byte
        # Use code_bytes for content
        content = code_bytes[start_byte:end_byte].decode('utf8', errors='ignore')

        content = code_bytes[start_byte:end_byte].decode('utf8', errors='ignore')
    
        # NEW CODE: Fix first line indentation
        original_lines = code.split('\n')
        if line_start < len(original_lines):
            original_line = original_lines[line_start]
            indent = original_line[:len(original_line)-len(original_line.lstrip())]
            content_lines = content.split('\n')
            if content_lines:
                # Reindent first line
                content_lines[0] = indent + content_lines[0].lstrip()
                content = '\n'.join(content_lines)

        docstring = element_to_docstring.get(actual_node, '')

        elements = []
        body_block = next((c for c in actual_node.children if c.type == 'block'), None)
        if body_block:
            for child in body_block.children:
                if child.type in ['function_definition', 'class_definition', 'decorated_definition']:
                    elem = process_element(child, identifier)
                    if elem:
                        elements.append(elem)
        return Element(
            identifier=identifier,
            content=content,
            description=docstring,
            line_start=line_start,
            embedding=None,
            elements=elements
        )

    top_elements = []
    for child in root_node.children:
        if child.type in ['class_definition', 'function_definition', 'decorated_definition']:
            element = process_element(child)
            if element:
                top_elements.append(element)

    return top_elements