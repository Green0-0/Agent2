from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List, Dict, Tuple
from agent2.element import Element

# WARNING: BUGS, IDENTIFIER DOESN'T CONSIDER OVERLOADS, DECORATORS ARENT CACLCULATED INTO START LINES...
# SEE test_csharp_parser.py

def parse_csharp_elements(code: str) -> List[Element]:
    parser = get_parser('c_sharp')
    code_bytes = code.encode('utf8')  # Encode once here
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    
    lines = code.split('\n')
    
    # Collect XML doc comments with their starting line numbers
    element_docstrings: Dict[int, Tuple[int, str]] = {}
    
    # First process XML comments
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('///'):
            # Start of a doc comment block
            start_line = i
            doc_lines = [lines[i]]
            i += 1
            
            # Collect consecutive doc comment lines
            while i < len(lines) and lines[i].strip().startswith('///'):
                doc_lines.append(lines[i])
                i += 1
                
            # The element is on the line after the comment block
            target_line = i
            if target_line < len(lines):
                element_docstrings[target_line] = (start_line, '\n'.join(doc_lines))
        else:
            i += 1
    
    # Track method signatures to detect overloads
    method_signatures = {}
    
    # Helper to get parameter type signature for method overloads
    def get_parameter_types(node):
        param_list = next((c for c in node.children if c.type == 'parameter_list'), None)
        if not param_list:
            return []
        
        types = []
        for child in param_list.children:
            if child.type == 'parameter':
                type_node = None
                for c in child.children:
                    if c.type in ['predefined_type', 'identifier', 'nullable_type', 'array_type', 'generic_name']:
                        type_node = c
                        break
                
                if type_node:
                    param_type = code_bytes[type_node.start_byte:type_node.end_byte].decode('utf8', errors='ignore')
                    types.append(param_type)
        
        return types
    
    # Collect method signatures to identify overloads
    def collect_method_signatures(node, path=""):
        if node.type in ['class_declaration', 'struct_declaration', 'interface_declaration']:
            name_node = next((c for c in node.children if c.type == 'identifier'), None)
            if name_node:
                name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
                new_path = f"{path}.{name}" if path else name
                
                body_node = next((c for c in node.children if c.type == 'declaration_list'), None)
                if body_node:
                    for child in body_node.children:
                        collect_method_signatures(child, new_path)
        
        elif node.type in ['method_declaration', 'constructor_declaration']:
            name_node = next((c for c in node.children if c.type == 'identifier'), None)
            if name_node:
                name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
                method_path = f"{path}.{name}" if path else name
                
                param_types = get_parameter_types(node)
                
                if method_path not in method_signatures:
                    method_signatures[method_path] = []
                method_signatures[method_path].append(param_types)
        
        elif node.type == 'namespace_declaration':
            name_node = next((c for c in node.children if c.type == 'identifier'), None)
            if name_node:
                namespace = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
                
                body_node = next((c for c in node.children if c.type == 'declaration_list'), None)
                if body_node:
                    for child in body_node.children:
                        collect_method_signatures(child, namespace)
    
    # Run first pass to collect method signatures
    collect_method_signatures(root_node)
    
    # Process elements with attributes and docstrings
    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        if node.type not in [
            'class_declaration', 'struct_declaration', 'interface_declaration',
            'method_declaration', 'constructor_declaration', 'property_declaration',
            'enum_declaration', 'namespace_declaration'
        ]:
            return None
        
        # Extract name
        name_node = next((c for c in node.children if c.type == 'identifier'), None)
        if not name_node:
            return None
        
        name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
        
        # Build identifier
        identifier = f"{parent_identifier}.{name}" if parent_identifier else name
        
        # For methods, check if overloaded and include parameters if needed
        if node.type in ['method_declaration', 'constructor_declaration']:
            if identifier in method_signatures and len(method_signatures[identifier]) > 1:
                # This is an overloaded method, add parameter types to identifier
                param_types = get_parameter_types(node)
                if param_types:
                    param_str = ', '.join(param_types)
                    identifier = f"{identifier}({param_str})"
        
        # Get attributes (decorators)
        attributes = []
        current = node.prev_sibling
        while current and current.type == 'attribute_list':
            attributes.insert(0, current)  # Insert at beginning to maintain order
            current = current.prev_sibling
        
        # Determine the actual start line including attributes and doc comments
        node_start_line = node.start_point[0]
        
        # Find all preceding whitespace, attributes, and documentation
        line_start = node_start_line
        
        # If we have attributes, use their start line
        if attributes:
            line_start = min(line_start, attributes[0].start_point[0])
        
        # Check if docstring exists for this node
        docstring = ""
        if node_start_line in element_docstrings:
            doc_start_line, doc_text = element_docstrings[node_start_line]
            line_start = min(line_start, doc_start_line)
            docstring = doc_text
        
        # Get content with attributes
        start_byte = node.start_byte
        if attributes:
            start_byte = attributes[0].start_byte
        
        content = code_bytes[start_byte:node.end_byte].decode('utf8', errors='ignore')
        
        # Fix first line indentation
        if 0 <= line_start < len(lines):
            original_line = lines[line_start]
            indent = original_line[:len(original_line)-len(original_line.lstrip())]
            content_lines = content.split('\n')
            if content_lines:
                # Reindent first line
                content_lines[0] = indent + content_lines[0].lstrip()
                content = '\n'.join(content_lines)
        
        # Process child elements
        elements = []
        body_node = next((c for c in node.children if c.type == 'declaration_list'), None)
        if body_node:
            for child in body_node.children:
                element = process_element(child, identifier)
                if element:
                    elements.append(element)
        
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
        element = process_element(child)
        if element:
            top_elements.append(element)
    
    return top_elements
