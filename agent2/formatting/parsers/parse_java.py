from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List, Dict, Tuple
from agent2.element import Element

# WARNING: MAY CONTAIN BUGS, DID NOT THOROUGHLY CHECK, GOOD AT FIRST GLANCE

def parse_java_elements(code: str) -> List[Element]:
    parser = get_parser('java')
    code_bytes = code.encode('utf8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    
    # Split code into lines for easier processing
    code_lines = code.split('\n')
    
    # Mapping of line number to byte offset at start of line
    line_to_byte = [0]
    offset = 0
    for line in code_lines:
        offset += len(line) + 1  # +1 for newline character
        line_to_byte.append(offset)
    
    # Track methods that need parameter disambiguation
    method_counts: Dict[str, int] = {}
    
    # First pass: identify overloaded methods
    def mark_overloaded_methods(node: Node, prefix: str = ""):
        if node.type not in ['class_declaration', 'interface_declaration', 'enum_declaration']:
            return
            
        # Get class name
        name = ""
        for child in node.children:
            if child.type == 'identifier':
                name = code_bytes[child.start_byte:child.end_byte].decode('utf8', errors='ignore')
                break
        
        if not name:
            return
            
        class_path = f"{prefix}.{name}" if prefix else name
        
        # Find body node
        body = None
        for child in node.children:
            if child.type in ['class_body', 'interface_body', 'enum_body']:
                body = child
                break
        
        if not body:
            return
        
        # Count method declarations
        for child in body.children:
            if child.type == 'method_declaration':
                method_name = ""
                for mchild in child.children:
                    if mchild.type == 'identifier':
                        method_name = code_bytes[mchild.start_byte:mchild.end_byte].decode('utf8', errors='ignore')
                        break
                
                if method_name:
                    method_path = f"{class_path}.{method_name}"
                    method_counts[method_path] = method_counts.get(method_path, 0) + 1
            
            # Recursively process nested classes
            elif child.type in ['class_declaration', 'interface_declaration', 'enum_declaration']:
                mark_overloaded_methods(child, class_path)
    
    # Run first pass to identify all overloaded methods
    for child in root_node.children:
        if child.type in ['class_declaration', 'interface_declaration', 'enum_declaration']:
            mark_overloaded_methods(child)
    
    # Get parameter signature for method overloads
    def get_parameter_signature(node: Node) -> str:
        for child in node.children:
            if child.type == 'formal_parameters':
                param_types = []
                for param in child.children:
                    if param.type == 'formal_parameter':
                        for pc in param.children:
                            if pc.type == 'type':
                                param_type = code_bytes[pc.start_byte:pc.end_byte].decode('utf8', errors='ignore')
                                param_types.append(param_type)
                                break
                
                return f"({', '.join(param_types)})"
        
        return "()"
    
    # Find JavaDoc comment and its start line
    def find_javadoc(node: Node) -> Tuple[str, int]:
        """Find JavaDoc comment before the node"""
        # Get node start line considering modifiers
        line_start = node.start_point[0]
        for child in node.children:
            if child.type == 'modifiers':
                line_start = min(line_start, child.start_point[0])
        
        # Check previous lines for JavaDoc
        current_line = line_start - 1
        
        # Skip whitespace
        while current_line >= 0 and not code_lines[current_line].strip():
            current_line -= 1
        
        if current_line < 0:
            return "", -1
            
        # Look for JavaDoc markers
        javadoc_lines = []
        in_javadoc = False
        javadoc_start = -1
        
        # Scan backwards to find complete JavaDoc
        while current_line >= 0:
            line = code_lines[current_line]
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                current_line -= 1
                continue
            
            # Check for JavaDoc markers
            if '*/' in stripped:  # End of comment block
                in_javadoc = True
                javadoc_lines.insert(0, line)
            elif in_javadoc and '/**' in stripped:  # Start of JavaDoc
                javadoc_lines.insert(0, line)
                javadoc_start = current_line
                break
            elif in_javadoc:  # Inside JavaDoc
                javadoc_lines.insert(0, line)
            else:  # Not in a JavaDoc comment
                break
            
            current_line -= 1
        
        if javadoc_start >= 0:
            return '\n'.join(javadoc_lines), javadoc_start
        
        return "", -1
    
    # Process an element node
    def process_element(node: Node, parent_path: str = "") -> Optional[Element]:
        if node.type not in ['class_declaration', 'method_declaration', 'constructor_declaration', 
                             'interface_declaration', 'enum_declaration']:
            return None
        
        # Get name
        name = ""
        for child in node.children:
            if child.type == 'identifier':
                name = code_bytes[child.start_byte:child.end_byte].decode('utf8', errors='ignore')
                break
        
        if not name:
            return None
        
        # Build identifier
        if node.type in ['method_declaration', 'constructor_declaration']:
            method_path = f"{parent_path}.{name}" if parent_path else name
            
            # Add parameters for overloaded methods and constructors
            if node.type == 'constructor_declaration' or method_counts.get(method_path, 0) > 1:
                params = get_parameter_signature(node)
                identifier = f"{parent_path}.{name}{params}" if parent_path else f"{name}{params}"
            else:
                identifier = f"{parent_path}.{name}" if parent_path else name
        else:
            identifier = f"{parent_path}.{name}" if parent_path else name
        
        # Find element start line and byte considering annotations/modifiers
        line_start = node.start_point[0]
        byte_start = node.start_byte
        
        for child in node.children:
            if child.type == 'modifiers':
                line_start = min(line_start, child.start_point[0])
                byte_start = min(byte_start, child.start_byte)
        
        # Find JavaDoc comment
        javadoc, javadoc_line = find_javadoc(node)
        
        # If JavaDoc exists, update start line and byte
        if javadoc_line >= 0:
            line_start = javadoc_line
            byte_start = line_to_byte[javadoc_line]
        
        # Get content
        content = code[byte_start:node.end_byte]
        
        # Process nested elements
        elements = []
        if node.type in ['class_declaration', 'interface_declaration', 'enum_declaration']:
            body = None
            for child in node.children:
                if child.type in ['class_body', 'interface_body', 'enum_body']:
                    body = child
                    break
            
            if body:
                for child in body.children:
                    if child.type in ['class_declaration', 'method_declaration', 
                                    'constructor_declaration', 'interface_declaration',
                                    'enum_declaration']:
                        elem = process_element(child, identifier)
                        if elem:
                            elements.append(elem)
        
        return Element(
            identifier=identifier,
            content=content,
            description=javadoc,
            line_start=line_start,
            embedding=None,
            elements=elements
        )
    
    # Process top-level elements
    top_elements = []
    for child in root_node.children:
        if child.type in ['class_declaration', 'interface_declaration', 'enum_declaration']:
            element = process_element(child)
            if element:
                top_elements.append(element)
    
    return top_elements
