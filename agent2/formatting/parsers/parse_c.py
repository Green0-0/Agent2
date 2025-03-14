from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List
from agent2.element import Element

# WARNING: COMPLETELY BROKEN

def parse_c_elements(code: str) -> List[Element]:
    """
    Parse C code into a recursive tree of Element objects
    
    Args:
        code: String containing C source code
        
    Returns:
        List of top-level Element objects with nested elements
    """
    parser = get_parser('c')
    code_bytes = code.encode('utf8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node

    # Collect all comments
    comments = []
    
    def traverse_for_comments(node: Node):
        if node.type == 'comment':
            comments.append((
                node.start_point[0],  # line number
                code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
            ))
        for child in node.children:
            traverse_for_comments(child)
    
    traverse_for_comments(root_node)
    comments.sort(key=lambda x: x[0])
    
    def find_docstring(node_line: int) -> str:
        """Find comments that might serve as docstring for an element starting at node_line"""
        relevant_comments = []
        
        # Find the end index of comments that appear before node_line
        end_idx = 0
        while end_idx < len(comments) and comments[end_idx][0] < node_line:
            end_idx += 1
        
        # Go backwards to collect consecutive comments 
        idx = end_idx - 1
        while idx >= 0:
            comment_line, comment_text = comments[idx]
            
            # Stop if we hit a large gap between comments or the node
            if idx < end_idx - 1 and comment_line < comments[idx + 1][0] - 1:
                break
            if comment_line < node_line - 3:  # Assume docstring is within 3 lines of the element
                break
                
            # Clean up comment formatting
            if comment_text.startswith('/*') and comment_text.endswith('*/'):
                cleaned = comment_text[2:-2].strip()
            elif comment_text.startswith('//'):
                cleaned = comment_text[2:].strip()
            else:
                cleaned = comment_text.strip()
                
            relevant_comments.insert(0, cleaned)
            idx -= 1
        
        return "\n".join(relevant_comments)
    
    def get_node_text(node: Node) -> str:
        """Extract text from a node"""
        return code_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
    
    def extract_function_info(node: Node) -> tuple[Optional[str], Optional[str]]:
        """Extract function name and parameter types"""
        # Find the declarator which contains the function name and params
        declarator = None
        for child in node.children:
            if child.type in ['function_declarator', 'declarator']:
                declarator = child
                break
        
        if not declarator:
            return None, None
            
        # Find the function name
        name = None
        current = declarator
        while current and not name:
            for child in current.children:
                if child.type == 'identifier':
                    name = get_node_text(child)
                    break
            
            if not name:
                deeper = None
                for child in current.children:
                    if 'declarator' in child.type:
                        deeper = child
                        break
                        
                if deeper:
                    current = deeper
                else:
                    break
        
        # Find the parameter list
        param_list = None
        current = declarator
        while current and not param_list:
            for child in current.children:
                if child.type == 'parameter_list':
                    param_list = child
                    break
            
            if not param_list:
                deeper = None
                for child in current.children:
                    if 'declarator' in child.type:
                        deeper = child
                        break
                        
                if deeper:
                    current = deeper
                else:
                    break
        
        # If no parameter list found
        if not param_list:
            return name, None
            
        # Extract parameter types
        param_types = []
        for child in param_list.children:
            if child.type == 'parameter_declaration':
                # Try to get a simplified type representation
                type_text = []
                for param_child in child.children:
                    if param_child.type in ['primitive_type', 'type_identifier']:
                        type_text.append(get_node_text(param_child))
                
                if type_text:
                    param_types.append(" ".join(type_text).strip())
                else:
                    # If no simple type found, use the whole parameter declaration
                    param_types.append("unknown")
            elif child.type == 'identifier' and get_node_text(child) == 'void':
                # Special case for void parameter
                return name, ""
                
        return name, ", ".join(param_types)
    
    def extract_struct_enum_union_name(node: Node) -> str:
        """Extract the name of a struct, enum, or union"""
        for child in node.children:
            if child.type == 'type_identifier':
                return get_node_text(child)
                
        # Anonymous struct/enum/union
        return f"anonymous_{node.type.split('_')[0]}"
    
    def extract_typedef_name(node: Node) -> Optional[str]:
        """Extract the name defined in a typedef"""
        # In a typedef, the last identifier is typically the new type name
        identifiers = []
        for child in node.children:
            if child.type in ['type_identifier', 'identifier']:
                identifiers.append(get_node_text(child))
                
        if identifiers:
            return identifiers[-1]
        return None
    
    def is_function_declaration(node: Node) -> bool:
        """Check if a declaration node is a function declaration"""
        if node.type != 'declaration':
            return False
            
        # Look for a function declarator
        for child in node.children:
            if child.type in ['init_declarator', 'declarator']:
                # Check if this declarator or its children contain a function_declarator
                stack = [child]
                while stack:
                    current = stack.pop()
                    if current.type == 'function_declarator':
                        return True
                    stack.extend([c for c in current.children if 'declarator' in c.type])
                        
        return False
    
    def is_typedef_declaration(node: Node) -> bool:
        """Check if a declaration node is a typedef"""
        if node.type != 'declaration':
            return False
            
        # Check for 'typedef' storage class specifier
        for child in node.children:
            if child.type == 'storage_class_specifier' and get_node_text(child) == 'typedef':
                return True
                
        return False
    
    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        """Process a C element node and create an Element"""
        if node.type not in ['function_definition', 'declaration', 'struct_specifier', 'enum_specifier', 'union_specifier']:
            return None
            
        name = None
        params = None
        
        # Extract name and parameters based on node type
        if node.type == 'function_definition':
            name, params = extract_function_info(node)
        elif node.type == 'declaration':
            if is_function_declaration(node):
                name, params = extract_function_info(node)
            elif is_typedef_declaration(node):
                name = extract_typedef_name(node)
            else:
                return None  # Regular variable declaration, not an element we track
        elif node.type in ['struct_specifier', 'enum_specifier', 'union_specifier']:
            name = extract_struct_enum_union_name(node)
        
        if not name:
            return None
            
        # Create the identifier
        if params is not None:  # Function
            identifier = f"{parent_identifier}.{name}({params})" if parent_identifier else f"{name}({params})"
        else:  # Non-function
            identifier = f"{parent_identifier}.{name}" if parent_identifier else name
        
        line_start = node.start_point[0]
        content = get_node_text(node)
        
        # Fix first line indentation
        original_lines = code.split('\n')
        if line_start < len(original_lines):
            original_line = original_lines[line_start]
            indent = original_line[:len(original_line)-len(original_line.lstrip())]
            content_lines = content.split('\n')
            if content_lines:
                content_lines[0] = indent + content_lines[0].lstrip()
                content = '\n'.join(content_lines)
        
        docstring = find_docstring(line_start)
        
        # Find nested elements
        elements = []
        
        # Check for compound statement (function body)
        compound_statement = None
        if node.type == 'function_definition':
            for child in node.children:
                if child.type == 'compound_statement':
                    compound_statement = child
                    break
        
        # Process nested elements
        if compound_statement:
            for child in compound_statement.children:
                if child.type in ['function_definition', 'declaration', 'struct_specifier', 'enum_specifier', 'union_specifier']:
                    elem = process_element(child, identifier)
                    if elem:
                        elements.append(elem)
        
        # Also check for nested types in struct/union/enum
        if node.type in ['struct_specifier', 'union_specifier', 'enum_specifier']:
            field_list = None
            for child in node.children:
                if child.type.endswith('_list'):
                    field_list = child
                    break
                    
            if field_list:
                for child in field_list.children:
                    if child.type in ['struct_specifier', 'union_specifier', 'enum_specifier', 'declaration']:
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
    
    # Process all top-level elements
    top_elements = []
    for child in root_node.children:
        if child.type in ['function_definition', 'declaration', 'struct_specifier', 'enum_specifier', 'union_specifier']:
            element = process_element(child)
            if element:
                top_elements.append(element)
    
    return top_elements
