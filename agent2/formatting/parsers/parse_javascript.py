from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List, Dict, Set, Tuple
from agent2.element import Element

# WARNING: MAY CONTAIN BUGS, DID NOT THOROUGHLY CHECK, GOOD AT FIRST GLANCE

def parse_javascript_elements(code: str) -> List[Element]:
    """
    Parse JavaScript code into a recursive tree of Element objects
    
    Args:
        code: JavaScript code as a string
        
    Returns:
        List of top-level Element objects, each containing nested elements
    """
    parser = get_parser('javascript')
    code_bytes = code.encode('utf8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node

    # Track JSDoc comments with their start line
    jsdoc_by_line: Dict[int, Tuple[str, int]] = {}
    
    # Track function names within each scope to detect duplicate names
    function_names_by_scope: Dict[str, Set[str]] = {}
    
    def collect_jsdoc_comments(node: Node):
        """Find all JSDoc comments in the tree"""
        if node.type == 'comment':
            text = code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore').strip()
            if text.startswith('/**') and text.endswith('*/'):
                # Store by the line after the comment ends, also saving the start line
                jsdoc_by_line[node.end_point[0] + 1] = (text, node.start_point[0])
        
        for child in node.children:
            collect_jsdoc_comments(child)
    
    # Collect all JSDoc comments
    collect_jsdoc_comments(root_node)
    
    def get_jsdoc_for_node(node: Node) -> Tuple[str, Optional[int]]:
        """Get the JSDoc comment and its start line for a node"""
        line = node.start_point[0]
        if line in jsdoc_by_line:
            return jsdoc_by_line[line]
        return ("", None)
    
    def get_element_name(node: Node) -> Optional[str]:
        """Extract the name of a code element node"""
        if node.type in ['function_declaration', 'class_declaration']:
            name_node = next((c for c in node.children if c.type == 'identifier'), None)
            if name_node:
                return code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
        
        elif node.type == 'method_definition':
            name_node = next((c for c in node.children if c.type in ['property_identifier', 'string']), None)
            if name_node:
                name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
                # Clean up string property names
                if name_node.type == 'string':
                    if (name.startswith('"') and name.endswith('"')) or (name.startswith("'") and name.endswith("'")):
                        name = name[1:-1]
                return name
        
        elif node.type in ['function', 'arrow_function', 'class']:
            # Variable declaration
            parent = node.parent
            if parent and parent.type == 'variable_declarator':
                name_node = next((c for c in parent.children if c.type == 'identifier'), None)
                if name_node:
                    return code_bytes[name_node.start_byte:name_node.end_byte].decode('utf8', errors='ignore')
            
            # Object method
            elif parent and parent.type == 'pair':
                key_node = next((c for c in parent.children if c.type in ['property_identifier', 'string']), None)
                if key_node:
                    name = code_bytes[key_node.start_byte:key_node.end_byte].decode('utf8', errors='ignore')
                    # Clean up string property names
                    if key_node.type == 'string':
                        if (name.startswith('"') and name.endswith('"')) or (name.startswith("'") and name.endswith("'")):
                            name = name[1:-1]
                    return name
        
        return None
    
    def get_parameters_string(node: Node) -> str:
        """Get the parameters string for a function node"""
        if node.type in ['function_declaration', 'method_definition', 'function', 'arrow_function']:
            params_node = next((c for c in node.children if c.type == 'formal_parameters'), None)
            if params_node:
                return code_bytes[params_node.start_byte:params_node.end_byte].decode('utf8', errors='ignore')
        return "()"
    
    def track_function_name(scope_id: str, name: str):
        """Track function names within a scope to detect duplicates"""
        if scope_id not in function_names_by_scope:
            function_names_by_scope[scope_id] = set()
        function_names_by_scope[scope_id].add(name)
    
    def has_duplicate_name(scope_id: str, name: str) -> bool:
        """Check if a function name is duplicated within its scope"""
        return scope_id in function_names_by_scope and name in function_names_by_scope[scope_id]
    
    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        """Process a code element node into an Element object"""
        if node.type not in [
            'function_declaration', 'class_declaration', 'method_definition',
            'function', 'arrow_function', 'class'
        ]:
            return None
        
        # Get the base name
        name = get_element_name(node)
        if not name:
            return None
        
        # Track function names in their parent scope
        scope_id = parent_identifier if parent_identifier else "root"
        track_function_name(scope_id, name)
        
        # Build the identifier path
        identifier = f"{parent_identifier}.{name}" if parent_identifier else name
        
        # For methods, include parameters if there are duplicate names in this scope
        # This helps distinguish between functions with the same name
        if node.type in ['function_declaration', 'method_definition', 'function', 'arrow_function']:
            if has_duplicate_name(scope_id, name):
                params = get_parameters_string(node)
                identifier = f"{identifier}{params}"
        
        # Get the JSDoc comment and its start line
        description, jsdoc_start_line = get_jsdoc_for_node(node)
        
        # Get line start (zero-indexed)
        # Use JSDoc comment start line if available
        line_start = jsdoc_start_line if jsdoc_start_line is not None else node.start_point[0]
        
        # Get the complete content
        content = code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
        
        # Fix first line indentation to preserve formatting
        original_lines = code.split('\n')
        if node.start_point[0] < len(original_lines):  # Use node's start line for indentation
            original_line = original_lines[node.start_point[0]]
            indent = original_line[:len(original_line)-len(original_line.lstrip())]
            content_lines = content.split('\n')
            if content_lines:
                content_lines[0] = indent + content_lines[0].lstrip()
                content = '\n'.join(content_lines)
        
        # Process child elements
        elements = []
        
        if node.type in ['class_declaration', 'class']:
            # Process class methods
            class_body = next((c for c in node.children if c.type == 'class_body'), None)
            if class_body:
                for child in class_body.children:
                    if child.type == 'method_definition':
                        element = process_element(child, identifier)
                        if element:
                            elements.append(element)
        
        elif node.type in ['function_declaration', 'method_definition', 'function', 'arrow_function']:
            # Process function body elements
            body = next((c for c in node.children if c.type == 'statement_block'), None)
            if body:
                for child in body.children:
                    # Direct function/class declarations
                    if child.type in ['function_declaration', 'class_declaration']:
                        element = process_element(child, identifier)
                        if element:
                            elements.append(element)
                    
                    # Variable declarations with functions/classes
                    elif child.type in ['lexical_declaration', 'variable_declaration']:
                        for declarator in [c for c in child.children if c.type == 'variable_declarator']:
                            for value in declarator.children:
                                if value.type in ['function', 'arrow_function', 'class']:
                                    element = process_element(value, identifier)
                                    if element:
                                        elements.append(element)
                    
                    # Object literals with methods
                    elif child.type == 'expression_statement':
                        for expr in child.children:
                            if expr.type in ['assignment_expression', 'binary_expression']:
                                for subexpr in expr.children:
                                    if subexpr.type == 'object':
                                        for pair in [c for c in subexpr.children if c.type == 'pair']:
                                            value = next((c for c in pair.children if c.type in ['function', 'arrow_function']), None)
                                            if value:
                                                element = process_element(value, identifier)
                                                if element:
                                                    elements.append(element)
        
        return Element(
            identifier=identifier,
            content=content,
            description=description,
            line_start=line_start,
            embedding=None,
            elements=elements
        )
    
    # Find and process all top-level elements
    top_elements = []
    
    for child in root_node.children:
        # Direct function/class declarations
        if child.type in ['function_declaration', 'class_declaration']:
            element = process_element(child)
            if element:
                top_elements.append(element)
        
        # Variable declarations with functions/classes
        elif child.type in ['lexical_declaration', 'variable_declaration']:
            for declarator in [c for c in child.children if c.type == 'variable_declarator']:
                for value in declarator.children:
                    if value.type in ['function', 'arrow_function', 'class']:
                        element = process_element(value)
                        if element:
                            top_elements.append(element)
        
        # Export statements
        elif child.type == 'export_statement':
            for subchild in child.children:
                if subchild.type in ['function_declaration', 'class_declaration']:
                    element = process_element(subchild)
                    if element:
                        top_elements.append(element)
                elif subchild.type in ['lexical_declaration', 'variable_declaration']:
                    for declarator in [c for c in subchild.children if c.type == 'variable_declarator']:
                        for value in declarator.children:
                            if value.type in ['function', 'arrow_function', 'class']:
                                element = process_element(value)
                                if element:
                                    top_elements.append(element)
        
        # Object literals with methods
        elif child.type == 'expression_statement':
            for expr in child.children:
                if expr.type == 'assignment_expression':
                    right = next((c for c in expr.children if c.type == 'object'), None)
                    if right:
                        for pair in [c for c in right.children if c.type == 'pair']:
                            value = next((c for c in pair.children if c.type in ['function', 'arrow_function']), None)
                            if value:
                                element = process_element(value)
                                if element:
                                    top_elements.append(element)
    
    return top_elements
