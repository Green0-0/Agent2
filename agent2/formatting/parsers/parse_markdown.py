from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser
from typing import Optional, List
from agent2.element import Element

def parse_markdown_elements(content: str) -> List[Element]:
    """
    Parse markdown content into a list of Element objects
    
    Args:
        content: String containing markdown content
        
    Returns:
        List of Element objects representing the markdown structure
    """
    parser = get_parser('markdown')
    content_bytes = content.encode('utf8')
    tree = parser.parse(content_bytes)
    root_node = tree.root_node
    
    def get_node_text(node: Node) -> str:
        """Extract text content from a node"""
        return content_bytes[node.start_byte:node.end_byte].decode('utf8', errors='ignore')
    
    # Map to store heading elements by level for building the hierarchy
    heading_level_map = {}
    # List to store all top-level elements
    top_elements = []
    
    def process_node(node: Node, parent_path: str = "") -> Optional[Element]:
        """Process a node and convert it to an Element if applicable"""
        element_type = None
        identifier = None
        description = ""
        sub_elements = []
        
        # Process different node types
        if node.type == 'atx_heading':
            # Find heading level and content
            level = 0
            for child in node.children:
                if child.type.startswith('atx_h') and child.type.endswith('_marker'):
                    level = int(child.type[5:6])
                    break
            
            # Extract heading text
            heading_text = ""
            for child in node.children:
                if child.type == 'inline':
                    heading_text = get_node_text(child).strip()
                    break
            
            if level > 0 and heading_text:
                # Create safe identifier from heading text
                safe_text = heading_text.replace(' ', '_').lower()
                for char in "!@#$%^&*()+=[]{}|\\:;\"'<>,.?/":
                    safe_text = safe_text.replace(char, '')
                
                # Build the full identifier path
                if parent_path:
                    identifier = f"{parent_path}.{safe_text}"
                else:
                    identifier = safe_text
                
                # Create element
                element = Element(
                    identifier=identifier,
                    content=get_node_text(node),
                    description=description,
                    line_start=node.start_point[0],
                    embedding=None,
                    elements=[]
                )
                
                # Store in level map for hierarchy building
                heading_level_map[level] = element
                
                # Find proper parent
                if level > 1 and level - 1 in heading_level_map:
                    heading_level_map[level - 1].elements.append(element)
                else:
                    top_elements.append(element)
                
                return element
                
        elif node.type == 'setext_heading':
            # Determine level and text
            level = 0
            heading_text = ""
            
            # Find the level (1 or 2)
            for child in node.children:
                if child.type == 'setext_h1_underline':
                    level = 1
                    break
                elif child.type == 'setext_h2_underline':
                    level = 2
                    break
            
            # Extract text from paragraph
            for child in node.children:
                if child.type == 'paragraph':
                    for para_child in child.children:
                        if para_child.type == 'inline':
                            heading_text = get_node_text(para_child).strip()
                            break
            
            if level > 0 and heading_text:
                # Create safe identifier from heading text
                safe_text = heading_text.replace(' ', '_').lower()
                for char in "!@#$%^&*()+=[]{}|\\:;\"'<>,.?/":
                    safe_text = safe_text.replace(char, '')
                
                # Build the full identifier path
                if parent_path:
                    identifier = f"{parent_path}.{safe_text}"
                else:
                    identifier = safe_text
                
                # Create element
                element = Element(
                    identifier=identifier,
                    content=get_node_text(node),
                    description=description,
                    line_start=node.start_point[0],
                    embedding=None,
                    elements=[]
                )
                
                # Store in level map for hierarchy building
                heading_level_map[level] = element
                
                # Find proper parent
                if level > 1 and level - 1 in heading_level_map:
                    heading_level_map[level - 1].elements.append(element)
                else:
                    top_elements.append(element)
                
                return element
                
        elif node.type == 'fenced_code_block':
            # Extract language if available
            language = "unknown"
            for child in node.children:
                if child.type == 'info_string':
                    lang_text = get_node_text(child).strip()
                    if lang_text:
                        language = lang_text
                    break
            
            element_type = f"code_{language}"
            
        elif node.type == 'pipe_table':
            element_type = "table"
            
        elif node.type == 'block_quote':
            element_type = "blockquote"
            
        elif node.type == 'list':
            element_type = "list"
            
        elif node.type == 'paragraph' and not parent_path:
            element_type = "paragraph"
        
        # Handle non-heading elements (code blocks, tables, lists, etc.)
        if element_type and not identifier:
            # Find the current heading level context
            current_level = 0
            current_path = parent_path
            
            # Create a unique identifier
            if not current_path:
                # Find the most specific heading this element belongs to
                for level in sorted(heading_level_map.keys(), reverse=True):
                    heading_element = heading_level_map[level]
                    if heading_element.line_start < node.start_point[0]:
                        current_path = heading_element.identifier
                        current_level = level
                        break
            
            # Generate identifier with counter
            counter_key = f"{element_type}_{current_path}"
            counter = 0
            while f"{current_path}.{element_type}_{counter}" in [e.identifier for e in top_elements]:
                counter += 1
            
            if current_path:
                identifier = f"{current_path}.{element_type}_{counter}"
            else:
                identifier = f"{element_type}_{counter}"
            
            # Create the element
            element = Element(
                identifier=identifier,
                content=get_node_text(node),
                description=description,
                line_start=node.start_point[0],
                embedding=None,
                elements=sub_elements
            )
            
            # Add to appropriate parent
            if current_path and current_level in heading_level_map:
                heading_level_map[current_level].elements.append(element)
            else:
                top_elements.append(element)
                
            return element
        
        return None
    
    # Process the document section by section
    def walk_and_process(node: Node, parent_path: str = ""):
        # For document node, process its children
        if node.type == 'document':
            for child in node.children:
                if child.type == 'section':
                    walk_and_process(child, parent_path)
        
        # For section node, process its children
        elif node.type == 'section':
            # First process any headings at this level
            for child in node.children:
                if child.type in ['atx_heading', 'setext_heading']:
                    element = process_node(child, parent_path)
                    if element:
                        # Update parent_path for subsequent elements
                        new_parent_path = element.identifier
                        
                        # Process other content within this section
                        for sibling in node.children:
                            if sibling != child and sibling.type not in ['section', 'atx_heading', 'setext_heading']:
                                process_node(sibling, new_parent_path)
                        
                        # Process nested sections
                        for sibling in node.children:
                            if sibling.type == 'section':
                                walk_and_process(sibling, new_parent_path)
                        
                        return  # Once we process the heading, we're done with this section
            
            # If there's no heading, process other elements directly
            for child in node.children:
                if child.type not in ['section']:
                    process_node(child, parent_path)
            
            # Process nested sections
            for child in node.children:
                if child.type == 'section':
                    walk_and_process(child, parent_path)
        
        # Directly process non-section nodes
        else:
            process_node(node, parent_path)
    
    # Start processing from the root
    walk_and_process(root_node)
    
    # Special case: if we have no sections or headings, process direct elements
    if not top_elements:
        for child in root_node.children:
            for grandchild in child.children:
                if grandchild.type in ['fenced_code_block', 'pipe_table', 'block_quote', 'list', 'paragraph']:
                    element = process_node(grandchild)
                    if element and element not in top_elements:
                        top_elements.append(element)
    
    # Sort by line number
    top_elements.sort(key=lambda e: e.line_start)
    
    return top_elements
