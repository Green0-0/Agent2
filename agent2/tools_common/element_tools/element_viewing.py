from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState
from agent2.formatting.autoformatter import enumerate_lines
from agent2.formatting.autoformatter import unindent
import re

from agent2.utils.embeddings_model_demo import EmbeddingsModel

def search_elements(state: AgentState, settings: ToolSettings, regex: str, path: str = "", extensions: str = None):
    """
    Recursively search along the path for elements matching a regex (case insensitive)
    
    Args:
        regex: Regular expression to match against
        path: Path of directory to search (defaults to root)
        extensions: Optional comma seperated string list of file extensions to filter
        
    Returns:
        Formatted string showing:
        - Matching files with match counts and matches
        - Error if invalid regex

    Example:
        Find places containing authentication patterns
    Tool Call:
        {"name": "search_files", "arguments": {"regex": "auth|login|session", "path": "src/auth/", "extensions": "py"}}
    """
    if "\\" in path:
        path = path.replace("\\", "/")
    if len(path) > 0 and path[0] == ".":
        path = path[1:]
    if len(path) > 0 and path[0] == "/":
        path = path[1:]

    try:
        pattern = re.compile(regex, flags=re.IGNORECASE)
    except re.error:
        raise ValueError(f"Invalid regex pattern: {regex}")
    
    files = state.workspace
    if path:
        files = [f for f in files if f.path.startswith(path)]
    if extensions:
        extensions = extensions.split(",")
        files = [f for f in files if any(f.extension.lower() in ext.lower() or ext.lower() in f.extension.lower() for ext in extensions)]

    if len (files) == 0:
        raise ValueError(f"Path {path} does not exist in workspace")
    all_elements = []
    for file in files:
        stack = list(file.elements)
        while stack:
            element = stack.pop()
            all_elements.append((element, file))
            stack.extend(element.elements)

    results = []
    for element, file in all_elements:
        elementlines = element.content.split('\n')
        # Enumerate lines if in settings
        if settings.number_lines:
            elementlines = [f"{i} {line}" for i, line in enumerate(elementlines, start=element.line_start)]
        matches = [line.strip() for line in elementlines if pattern.search(line)]
        if matches:
            doc = element.description if element.description else None
            if doc != None:
                # clean up docstring
                doc = unindent(doc)
                doclines = []
                for line in doc.splitlines():
                    line = line.strip()
                    if line != "" and line != "\"\"\"":
                        doclines.append(line)
                doc = "\n".join(doclines)
            results.append({
                'id': element.identifier,
                'doc': doc,
                'matches': matches,
                'count': len(matches),
                'true_count': len(matches),
                'path': file.path + f" (line {element.line_start})"
            })
    if len(results) == 0:
        return ("No matches found.", None, None)
    results.sort(key=lambda x: x['count'], reverse=True)
    total = len(results)
    results = results[:settings.max_search_result_listings]
    
    total_lines = sum(r['count'] for r in results)
    total_lines += sum(len(r['doc'].splitlines()) for r in results if r['doc'] != None)
    while total_lines > settings.max_search_result_lines:
        max_res = max(results, key=lambda x: x['count'])
        if max_res['count'] == 0:
            break
        max_res['matches'].pop()
        max_res['count'] -= 1
        total_lines -= 1
    
    while total_lines > settings.max_search_result_lines:
        # Remove last line from docstring
        max_res = max(results, key=lambda x: len(x['doc'].splitlines()) if x['doc'] != None else 0)
        if max_res['doc'] == None:
            break
        max_res['doc'] = "\n".join(max_res['doc'].splitlines()[:-1])
        total_lines -= 1

    formatted = [f"**Showing top {len(results)}/{total} matches:**"]
    for res in results:
        formatted.append(f"{res['path']}: {res['id']}: {res['true_count']} matches")
        if res['doc'] != None:
            formatted.append(f"{res['doc']}")
        formatted.extend(res['matches'])
        formatted.append("")
    
    return ("\n".join(formatted).strip(), None, None)

def view_element(state: AgentState, settings: ToolSettings, path: str, identifier: str):
    """
    View an element in a file. Make sure to specify the element path exactly; if you want to view the bar method within the foo class, use foo.bar. You should always view an element that you intend to modify, before you modify it.
    
    Args:
        identifier: Element identifier to view
    
    Returns:
        Formatted string showing:
        - The content of the element

    Example:
        View element auth
    Tool Call:
        {"name": "view_element", "arguments": {"path": "src/auth/auth.py", "identifier": "auth"}}
    """
    if "\\" in path:
        path = path.replace("\\", "/")
    if len(path) > 0 and path[0] == ".":
        path = path[1:]
    if len(path) > 0 and path[0] == "/":
        path = path[1:]

    file = next((f for f in state.workspace if f.path.lower() == path.lower()), None)
    if not file:
        raise ValueError(f"File {path} not found")
    
    all_elements = []
    stack = list(file.elements)
    while stack:
        element = stack.pop()
        all_elements.append(element)
        stack.extend(element.elements)
    
    element = next((e for e in all_elements if e.identifier.lower() == identifier.lower()), None)
    if not element:
        element = next((e for e in all_elements if identifier.lower() in e.identifier.lower()), None)
        if not element:
            element = next((e for e in all_elements if identifier.lower().split(".")[-1] in e.identifier.lower()), None)
        if not element:
            element = next((e for e in all_elements if e.identifier.lower().split(".")[-1] in identifier.lower()), None)
        if not element:
            raise ValueError(f"Element {identifier} not found in file {path}")
        else:
            raise ValueError(f"Element {identifier} not found in file {path}. Did you mean {element.identifier}?")
    if settings.secretly_save:
        if (file.path, element.identifier) not in state.saved_elements:
            state.saved_elements.append((file.path, element.identifier))

    if len(element.content.splitlines()) < settings.max_view_lines_start + settings.max_view_lines_end:
        return (element.to_string(number_lines=settings.number_lines, unindent_text=settings.unindent_inputs, mask_subelements = False), None, None)
    content = element.to_string(number_lines=settings.number_lines, unindent_text=settings.unindent_inputs)
    lines = content.splitlines()
    if len(lines) > settings.max_view_lines_end + settings.max_view_lines_start:
        lines = lines[:settings.max_view_lines_start] + ["..."] + lines[-settings.max_view_lines_end:] + ["\nNote: Showing only top and bottom " + str(settings.max_view_lines_start + settings.max_view_lines_end) + " lines to prevent context overflow."]
    content = "\n".join(lines)
    if len(element.elements) > 0:
        content += f"\n**This element has {len(element.elements)} sub-elements, you can use the view_element tool to view them, just make sure to specify the entire path, for instance, {element.elements[0].identifier}.**"
    return (content, None, None)

def view_file(state: AgentState, settings: ToolSettings, path: str):
    """
    View the general contents of a file.
    
    Args:
        path: File path

    Returns:
        Formatted string showing:
        - The content of the file

    Example:
        View file src/auth/auth.py

    Tool Call:
        {"name": "view_file", "arguments": {"path": "src/auth/auth.py"}}
    """
    if "\\" in path:
        path = path.replace("\\", "/")
    if len(path) > 0 and path[0] == ".":
        path = path[1:]
    if len(path) > 0 and path[0] == "/":
        path = path[1:]

    file = next((f for f in state.workspace if f.path.lower() == path.lower()), None)
    if not file:
        raise ValueError(f"File {path} not found")
    
    content = file.to_string(unindent_text=settings.unindent_inputs, number_lines=settings.number_lines)
    lines = content.splitlines()
    if len(lines) > settings.max_view_lines_end + settings.max_view_lines_start:
        lines = lines[:settings.max_view_lines_start] + ["..."] + lines[-settings.max_view_lines_end:] + ["\nNote: Showing only top and bottom " + str(settings.max_view_lines_start + settings.max_view_lines_end) + " lines to prevent context overflow."]
    content = "\n".join(lines)
    return (content, None, None)

def semantic_search_elements(state: AgentState, settings: ToolSettings, query: str, 
                            path: str = "", extensions: str = None) -> str:
    """
    Search for elements semantically matching query, sorted by similarity
    
    Args:
        query: Natural language query to match against
        path: Path prefix to filter files
        extensions: Optional comma separated string of file extensions to filter
        similarity_percent: Minimum similarity threshold (0-1)
        
    Returns:
        Formatted string showing:
        - Matching elements with similarity scores and descriptions
        - Respects max_search_result_listings and max_search_result_lines constraints
        - Error if no matches found

    Example:
        Find elements related to user authentication
    Tool Call:
        {"name": "semantic_search_elements", "arguments": {"query": "A class that manages user authentication", "path": "src/auth/", "extensions": "py,js"}}
    """
    from sentence_transformers import SentenceTransformer
    
    if "\\" in path:
        path = path.replace("\\", "/")
    if path.startswith((".", "/")):
        path = path.lstrip("./")
    
    # Filter files
    files = state.workspace
    if path:
        files = [f for f in files if f.path.startswith(path)]
    if extensions:
        extensions = extensions.split(",")
        files = [f for f in files if any(f.extension.lower() in ext.lower() 
                                        or ext.lower() in f.extension.lower() 
                                        for ext in extensions)]
    
    if not files:
        return (f"No files found matching path '{path}' and extensions '{extensions}'", None, None)
    
    # Generate embeddings if needed
    if settings.embeddings_model_path != None and settings.embeddings_model_path != "":
        if settings.embeddings_model == None:
            try:
                settings.embeddings_model = EmbeddingsModel(SentenceTransformer(settings.embeddings_model_path))
            except Exception as e:
                raise RuntimeError(f"Failed to load embeddings model: {e}. Use another tool instead.")
        settings.embeddings_model.create_docs(files)
    else:
        raise RuntimeError("Semantic search requires embeddings model, no embeddings model is configured. Use another tool instead.")
    
    # Get semantic matches
    matches = settings.embeddings_model.get_top_matches(
        files, query, 
        similarity_percent=settings.minimum_embeddings_similarity,
        max_count=100
    )

    if not matches:
        return (f"No elements semantically matching '{query}' found", None, None)
    
    # Prepare results with line numbering and doc cleaning
    results = []
    for match in matches:
        element = match['element']
        doc = element.description
        if doc:
            doc = unindent(doc)
            doc_lines = []
            for line in doc.splitlines():
                line = line.strip()
                if line and line not in ['"""', "'''", "/*", "*/"]:
                    doc_lines.append(line)
            doc = "\n".join(doc_lines)
        
        content_lines = element.content.split('\n')
        if settings.number_lines:
            content_lines = [f"{i} {line}" for i, line in 
                            enumerate(content_lines, start=element.line_start)]
        
        results.append({
            'id': element.identifier,
            'doc': doc,
            'content': content_lines,
            'similarity': match['similarity'],
            'path': match['file']
        })
    
    # Apply listing limits
    results.sort(key=lambda x: x['similarity'], reverse=True)
    total = len(results)
    results = results[:settings.max_search_result_listings]
    
    # Apply line limits
    total_lines = sum(len(res['content']) for res in results)
    total_lines += sum(len(res['doc'].splitlines()) for res in results if res['doc'])
    
    while total_lines > settings.max_search_result_lines and results:
        largest = max(results, key=lambda x: len(x['content']) + (len(x['doc'].splitlines()) if x['doc'] else 0))
        if len(largest['content']) > 0:
            largest['content'].pop()
            total_lines -= 1
        elif largest['doc']:
            doc_lines = largest['doc'].splitlines()
            if doc_lines:
                doc_lines.pop()
                largest['doc'] = '\n'.join(doc_lines)
                total_lines -= 1
        else:
            results.remove(largest)
    
    # Format output
    formatted = [f"**Showing top {len(results)}/{total} matches:**"]
    for res in results:
        header = f"{res['path']}:{res['id']} ({res['similarity']:.2f} similarity)"
        formatted.append(header)
        
        if res['doc']:
            formatted.append(res['doc'])
        
        formatted.append("")
    
    return ("\n".join(formatted).strip(), None, None)

def view_element_at(state: AgentState, settings: ToolSettings, path: str, line: int):
    """
    View the innermost element at a specific line in a file. The line is zero-indexed. This tool finds the deepest nested element at the given line and calls view_element for it.
    
    Args:
        path: Path to the file
        line: Zero-indexed line number in the file
    
    Returns:
        The output of view_element for the found element
    
    Example:
        View element at line 5 in src/app.py
    Tool Call:
        {"name": "view_element_at", "arguments": {"path": "src/app.py", "line": 5}}
    """
    # Normalize path
    if "\\" in path:
        path = path.replace("\\", "/")
    if path.startswith("."):
        path = path[1:]
    if path.startswith("/"):
        path = path[1:]
    
    # Find the file
    file = next((f for f in state.workspace if f.path.lower() == path.lower()), None)
    if not file:
        raise ValueError(f"File {path} not found")
    
    # Validate line number
    lines_in_file = len(file.updated_content.split('\n'))
    if line < 0 or line >= lines_in_file:
        raise ValueError(f"Line {line} is out of bounds for file {path} (0-based, total lines {lines_in_file})")
    
    # Find the innermost element
    best_element = None
    best_depth = -1
    stack = [(element, 0) for element in file.elements]  # (element, depth)
    
    while stack:
        element, depth = stack.pop()
        line_count = len(element.content.split('\n'))
        end_line = element.line_start + line_count - 1
        if element.line_start <= line <= end_line:
            if depth > best_depth:
                best_element = element
                best_depth = depth
            # Add children to stack with incremented depth
            stack.extend([(child, depth + 1) for child in element.elements])
    
    if not best_element:
        raise ValueError(f"No element found at line {line} in file {path}")
    
    # Call view_element with the found identifier
    return view_element(state, settings, path, best_element.identifier)