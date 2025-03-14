from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List
from agent2.element import Element

# WARNING: COMPLETELY BROKEN

def parse_cpp_elements(code: str) -> List[Element]:
    parser = get_parser('cpp')
    code_bytes = code.encode('utf8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node
    language = get_language('cpp')

    def get_docstring(element_node: Node) -> str:
        """Extracts preceding comments as docstring for an element node."""
        doc_lines = []
        prev_node = element_node.prev_named_sibling
        while prev_node and prev_node.type == 'comment':
            comment_text = code_bytes[prev_node.start_byte:prev_node.end_byte].decode('utf8', errors='ignore').strip()
            doc_lines.append(comment_text)
            prev_node = prev_node.prev_named_sibling
        doc_lines.reverse()
        return '\n'.join(doc_lines)

    def extract_parameters(parameters_node: Node) -> List[str]:
        """Extracts parameter types from a parameter_list node."""
        params = []
        for param_node in parameters_node.named_children:
            if param_node.type != 'parameter_declaration':
                continue
            
            declarator = None
            for child in param_node.children:
                if child.type in ['identifier', 'pointer_declarator', 'reference_declarator', 'array_declarator']:
                    declarator = child
                    break
            
            if declarator:
                type_end = declarator.start_byte
            else:
                type_end = param_node.end_byte
            
            param_type = code_bytes[param_node.start_byte:type_end].decode('utf8', errors='ignore').strip()
            params.append(param_type)
        return params

    def get_function_identifier(declarator: Node, parent_identifier: str) -> str:
        """Constructs the function identifier with parameters."""
        name = "anonymous"
        params_str = ""
        
        # Extract function name
        current_declarator = declarator
        while current_declarator.type in ['pointer_declarator', 'reference_declarator', 'array_declarator']:
            current_declarator = current_declarator.child_by_field_name('declarator') or current_declarator
        
        if current_declarator.type == 'qualified_identifier':
            name_nodes = [child for child in current_declarator.children if child.type == 'identifier']
            name = code_bytes[name_nodes[-1].start_byte:name_nodes[-1].end_byte].decode() if name_nodes else "anonymous"
        elif current_declarator.type == 'identifier':
            name = code_bytes[current_declarator.start_byte:current_declarator.end_byte].decode()
        
        # Extract parameters
        parameters_node = declarator.child_by_field_name('parameters')
        if parameters_node:
            params = extract_parameters(parameters_node)
            params_str = ', '.join(params)
        
        # Build identifier
        if parent_identifier:
            return f"{parent_identifier}::{name}({params_str})"
        return f"{name}({params_str})"

    def process_element(node: Node, parent_identifier: str = '') -> Optional[Element]:
        """Recursively processes C++ AST nodes into Element objects."""
        start_byte = node.start_byte
        line_start = node.start_point[0]
        elements = []
        docstring = get_docstring(node)

        # Handle namespaces
        if node.type == 'namespace_definition':
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None
            name = code_bytes[name_node.start_byte:name_node.end_byte].decode()
            identifier = f"{parent_identifier}{name}"
            
            # Process namespace body
            body = node.child_by_field_name('body')
            if body:
                for child in body.named_children:
                    elem = process_element(child, identifier)
                    if elem:
                        elements.append(elem)
            
            return Element(
                identifier=identifier,
                content=code_bytes[start_byte:node.end_byte].decode(),
                description=docstring,
                line_start=line_start,
                embedding=None,
                elements=elements
            )

        # Handle classes/structs
        elif node.type in ['class_specifier', 'struct_specifier']:
            name_node = node.child_by_field_name('name')
            if not name_node:
                return None
            name = code_bytes[name_node.start_byte:name_node.end_byte].decode()
            identifier = f"{parent_identifier}{name}"
            
            # Process class body
            body = node.child_by_field_name('body')
            if body:
                for child in body.named_children:
                    if child.type == 'field_declaration':
                        for grandchild in child.named_children:
                            elem = process_element(grandchild, identifier)
                            if elem:
                                elements.append(elem)
                    elif child.type in ['class_specifier', 'struct_specifier']:
                        elem = process_element(child, identifier)
                        if elem:
                            elements.append(elem)
            
            return Element(
                identifier=identifier,
                content=code_bytes[start_byte:node.end_byte].decode(),
                description=docstring,
                line_start=line_start,
                embedding=None,
                elements=elements
            )

        # Handle functions
        elif node.type == 'function_definition':
            declarator = node.child_by_field_name('declarator')
            if not declarator or declarator.type != 'function_declarator':
                return None
            
            # Handle attributes/decorators
            decorator_nodes = []
            current = node.prev_named_sibling
            while current and current.type in ['attribute_specifier', 'comment']:
                decorator_nodes.append(current)
                current = current.prev_named_sibling
            decorator_nodes.reverse()
            
            if decorator_nodes:
                start_byte = decorator_nodes[0].start_byte
                line_start = decorator_nodes[0].start_point[0]

            identifier = get_function_identifier(declarator, parent_identifier)
            return Element(
                identifier=identifier,
                content=code_bytes[start_byte:node.end_byte].decode(),
                description=docstring,
                line_start=line_start,
                embedding=None,
                elements=[]
            )

        return None

    top_elements = []
    for child in root_node.named_children:
        if elem := process_element(child):
            top_elements.append(elem)
    
    return top_elements