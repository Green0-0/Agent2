from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List
from agent2.element import Element

# WARNING: COMPLETELY BROKEN

def parse_ruby_elements(code: str) -> List[Element]:
    parser = get_parser('ruby')
    code_bytes = code.encode('utf8')  # Encode once here
    tree = parser.parse(code_bytes)
    root_node = tree.root_node

    # Map to store line -> comment text
    line_to_comment = {}
    
    # First pass: collect all comments
    def collect_comments(node):
        if node.type == 'comment':
            line = node.start_point[0]
            comment_text = code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
            # Remove # prefix and whitespace
            comment_text = comment_text.lstrip('#').strip()
            line_to_comment[line] = comment_text
        
        for child in node.children:
            collect_comments(child)
    
    collect_comments(root_node)
    
    # Function to get consecutive comments above a node
    def get_comments_above(node):
        start_line = node.start_point[0]
        comments = []
        current_line = start_line - 1
        
        # Collect consecutive comments
        while current_line in line_to_comment:
            comments.insert(0, line_to_comment[current_line])
            current_line -= 1
            
        if comments:
            return '\n'.join(comments)
        return ""
    
    # Helper to check if a method might be overloaded (has parameters)
    def get_method_parameters(node):
        for child in node.children:
            if child.type in ['method_parameters', 'parameters', 'parameter_list']:
                params = code_bytes[child.start_byte:child.end_byte].decode('utf8', errors='ignore')
                return params.strip()
        return ""
    
    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        # Handle different Ruby definition types
        if node.type not in ['module', 'class', 'method', 'singleton_method', 'singleton_class']:
            return None
        
        # Extract the element name based on node type
        name = None
        
        if node.type in ['module', 'class']:
            # Find the constant name for module/class
            for child in node.children:
                if child.type == 'constant':
                    name = code_bytes[child.start_byte:child.end_byte].decode('utf8', errors='ignore')
                    break
        elif node.type == 'method':
            # Find the method name
            for child in node.children:
                if child.type == 'identifier':
                    name = code_bytes[child.start_byte:child.end_byte].decode('utf8', errors='ignore')
                    
                    # Check for parameters (for overloaded methods)
                    params = get_method_parameters(node)
                    if params:
                        name = f"{name}({params})"
                    break
        elif node.type == 'singleton_method':
            # Class method
            for child in node.children:
                if child.type == 'identifier':
                    method_name = code_bytes[child.start_byte:child.end_byte].decode('utf8', errors='ignore')
                    name = f"self.{method_name}"
                    
                    # Check for parameters (for overloaded methods)
                    params = get_method_parameters(node)
                    if params:
                        name = f"{name}({params})"
                    break
        elif node.type == 'singleton_class':
            # class << self block
            name = "self"
        
        if not name:
            return None
            
        # Build the full identifier path
        identifier = f"{parent_identifier}.{name}" if parent_identifier else name
        
        line_start = node.start_point[0]
        
        # Get the full content
        content = code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
        
        # Fix indentation to preserve original formatting
        original_lines = code.split('\n')
        if line_start < len(original_lines):
            original_line = original_lines[line_start]
            indent = original_line[:len(original_line)-len(original_line.lstrip())]
            content_lines = content.split('\n')
            if content_lines:
                # Reindent first line
                content_lines[0] = indent + content_lines[0].lstrip()
                content = '\n'.join(content_lines)
        
        # Get docstring from comments above this element
        docstring = get_comments_above(node)
        
        # Process nested elements
        elements = []
        
        # Find the body node to process children
        body_node = None
        for child in node.children:
            if child.type in ['body', 'body_statement', 'begin', 'block']:
                body_node = child
                break
                
        if body_node:
            for child in body_node.children:
                if child.type in ['module', 'class', 'method', 'singleton_method', 'singleton_class']:
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
    
    # Process top-level elements
    top_elements = []
    for child in root_node.children:
        if child.type in ['module', 'class', 'method', 'singleton_method', 'singleton_class']:
            element = process_element(child)
            if element:
                top_elements.append(element)
                
    return top_elements
