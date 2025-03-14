from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState
from agent2.formatting.autoformatter import reindent, remove_codeblock, unenumerate_lines
from agent2.formatting.lookup import lookup_text
import re

def replace_lines(state: AgentState, settings: ToolSettings, path: str, line_start: int, line_end: int):
    """
    Replace lines in a file with the last code block you output. Make sure to include all the lines that need to be removed and substituted with the replacement code, which must be written in its entirety. Replace one group of lines at a time; output one code block for each group then immediately replace it.
    
    Args:
        path: File path
        line_start: Starting line number, inclusive
        line_end: Ending line number, inclusive
    
    Returns:
        Diff of the file, or failure

    Example:
        Assume you previously output ```python\n...i = 5...\n```. Replace lines 100-105 (line 105) of auth.py with this last output code block.
    Tool Call:
        {"name": "replace_lines", "arguments": {"path": "src/auth/auth.py", "line_start": 100, "line_end": 105}}
    """
    if state.last_code_block is None:    
        raise ValueError("No previous code block found!")
    return replace_lines_with(state, settings, path, line_start, line_end, state.last_code_block)

def replace_block(state: AgentState, settings: ToolSettings, path: str, block: str):
    """
    Replace a block in a file with the last code block you output. You must output the entire block being replaced, and every line that must be deleted. Replace one block of code at a time; output one code block for each block then immediately replace it.
    
    Args:
        path: File path
        block: Block to replace, every line must be typed in its entirety and matched exactly
    
    Returns:
        Diff of the file, or failure

    Example:
        Assume you previously output ```python\ndef login(auth, password):\n    i = 5```. Replace ```\ndef login():\n    i = 5``` in auth.py with this last output code block.
    Tool Call:
        {"name": "replace_block", "arguments": {"path": "src/auth/auth.py", "block": "def login():\\n    i = 5"}}
    """
    if state.last_code_block is None:    
        raise ValueError("No previous code block found!")
    return replace_block_with(state, settings, path, block, state.last_code_block)

def replace_element(state: AgentState, settings: ToolSettings, path: str, identifier: str):
    """
    Replace an element and all its subelements with the last code block you output. Always edit the innermost elements and not outer elements. Replace one element at a time; output one code block for each element then immediately replace it. Make sure to specify the element path exactly, and the entirety of the replacement code, otherwise it will be cut off; if you want to view the bar method within the foo class, use foo.bar.
    
    Args:
        path: File path
        identifier: Identifier of the element to replace
        replacement: String to replace lines with
    
    Returns:
        Diff of the file, or failure

    Example:
        Assume you previously output ```python\ndef auth(token, password):\n    i = 5```. Replace element auth in auth.py with the last code block output
    Tool Call:
        {"name": "replace_element_with", "arguments": {"path": "src/auth/auth.py", "identifier": "auth"}}
    """
    if state.last_code_block is None:    
        raise ValueError("No previous code block found!")
    return replace_element_with(state, settings, path, identifier, state.last_code_block)

def search_files(state: AgentState, settings: ToolSettings, regex: str, path: str = "", extensions: str = None):
    """
    Recursively search along the path for lines matching a regex (case insensitive)
    
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
        files = [f for f in files if f.path.lower().startswith(path.lower())]
    if extensions:
        extensions = extensions.split(",")
        files = [f for f in files if any(f.extension.lower() in ext.lower() or ext.lower() in f.extension.lower() for ext in extensions)]

    if len (files) == 0:
        raise ValueError(f"Path {path} does not exist in workspace")
    # Find regex matches
    results = []
    for f in files:
        all_matches = []
        content = f.content
        content = "\n".join([line.strip() for line in content.splitlines()])
        if settings.number_lines:
            content = enumerate_lines(content)
        for line in content.splitlines():
            if pattern.search(line):
                all_matches.append(line.strip())
        if len(all_matches) > 0:
            results.append((f.path, all_matches, len(all_matches)))
    if len(results) == 0:
        return ("No matches found.", None, None)
    results.sort(key=lambda x: x[2], reverse=True)
    total_results_count = len(results)
    results = results[:settings.max_search_result_listings]
    result_line_count = sum(num for _, _, num in results)
    while result_line_count > settings.max_search_result_lines:
        # Find the file with the most matches, remove the last match
        most_matches = max(results, key=lambda x: len(x[1]))
        most_matches[1].pop()
        result_line_count -= 1

    # Format results
    formatted_results = [f"**Showing top {len(results)}/{total_results_count} matches:**"]
    for match in results:
        formatted_results += [f"{match[0]}: {match[2]} matches"]
        for line in match[1]:
            formatted_results += [f"{line}"]
        formatted_results += [""]
    
    return ("\n".join(formatted_results).strip(), None, None)

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
