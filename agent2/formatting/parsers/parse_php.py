from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List
from agent2.element import Element

# WARNING: DOES NOT PROPERLY CONSIDER DOCSTRING INTO START LINE

def parse_php_elements(code: str) -> List[Element]:
    parser = get_parser('php')
    code_bytes = code.encode('utf8')  # Encode once here
    tree = parser.parse(code_bytes)
    root_node = tree.root_node

    language = get_language('php')
    doc_str_pattern = """
        (comment) @doc_comment
    """
    doc_str_query = language.query(doc_str_pattern)
    captures = doc_str_query.captures(root_node)

    element_to_docstring = {}
    for node, _ in captures:
        # Only consider PHPDoc style comments (/**...)
        comment_text = code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
        if not comment_text.strip().startswith('/**'):
            continue
            
        # Find the element this docstring documents
        current_node = node
        next_sibling = current_node.next_sibling
        while next_sibling and next_sibling.type in ['comment', 'text', '<?php']:
            next_sibling = next_sibling.next_sibling
        
        if next_sibling and next_sibling.type in ['class_declaration', 'method_declaration', 'function_declaration', 'interface_declaration', 'trait_declaration']:
            element_to_docstring[next_sibling] = comment_text

    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        actual_node = node
        attributes = []
        
        # Handle PHP attributes (similar to Python decorators)
        if node.type == 'attributed_declaration':
            # Find attributes
            for child in node.children:
                if child.type == 'attribute_list':
                    attributes.append(child)
                elif child.type in ['class_declaration', 'method_declaration', 'function_declaration', 'interface_declaration', 'trait_declaration']:
                    actual_node = child
                    break

        if actual_node.type not in ['class_declaration', 'method_declaration', 'function_declaration', 'interface_declaration', 'trait_declaration']:
            return None

        # Get name
        name_node = None
        for child in actual_node.children:
            if child.type == 'name':
                name_node = child
                break
                
        if not name_node:
            return None
            
        name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
        identifier = f"{parent_identifier}.{name}" if parent_identifier else name
        
        # Determine line_start (topmost line where element is relevant)
        line_start = actual_node.start_point[0]
        if attributes:
            # Use the topmost attribute's line
            line_start = min(attr.start_point[0] for attr in attributes)
        
        # Extract content including attributes
        start_byte = attributes[0].start_byte if attributes else actual_node.start_byte
        end_byte = actual_node.end_byte
        content = code_bytes[start_byte:end_byte].decode('utf8', errors='ignore')
        
        # Fix first line indentation to maintain original formatting
        original_lines = code.split('\n')
        if line_start < len(original_lines):
            original_line = original_lines[line_start]
            indent = original_line[:len(original_line)-len(original_line.lstrip())]
            content_lines = content.split('\n')
            if content_lines:
                content_lines[0] = indent + content_lines[0].lstrip()
                content = '\n'.join(content_lines)
        
        # Get docstring
        docstring = element_to_docstring.get(actual_node, '')
        
        # Process child elements recursively
        elements = []
        body_node = None
        for child in actual_node.children:
            if child.type in ['declaration_list', 'compound_statement']:
                body_node = child
                break
                
        if body_node:
            for child in body_node.children:
                if child.type in ['method_declaration', 'class_declaration', 'function_declaration', 'interface_declaration', 'trait_declaration', 'attributed_declaration']:
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
    
    # Find PHP code blocks
    program_nodes = [child for child in root_node.children if child.type == 'program']
    
    if program_nodes:
        for program_node in program_nodes:
            for child in program_node.children:
                if child.type in ['class_declaration', 'function_declaration', 'interface_declaration', 'trait_declaration', 'attributed_declaration']:
                    element = process_element(child)
                    if element:
                        top_elements.append(element)
    else:
        # Handle case where declarations might be directly under root
        for child in root_node.children:
            if child.type in ['class_declaration', 'function_declaration', 'interface_declaration', 'trait_declaration', 'attributed_declaration']:
                element = process_element(child)
                if element:
                    top_elements.append(element)

    return top_elements
