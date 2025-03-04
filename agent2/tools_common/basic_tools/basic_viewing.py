from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState
from agent2.formatting.autoformatter import enumerate_lines
from agent2.formatting.autoformatter import unindent
from agent2.utils.utils import get_overlaps
import re

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
        content = f.updated_content
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

def view_lines(state: AgentState, settings: ToolSettings, line_start: int, line_end: int, path: str):
    """
    View a range of lines in a file
    
    Args:
        line_start: Starting line number, inclusive
        line_end: Ending line number, inclusive
        path: File path to view
    
    Returns:
        Formatted string showing:
        - The content between the lines, inclusive of the lines

    Example:
        View lines 100-125 of auth.py
    Tool Call:
        {"name": "view_lines", "arguments": {"line_start": 100, "line_end": 125, "path": "src/auth/auth.py"}}
    """
    if "\\" in path:
        path = path.replace("\\", "/")
    if len(path) > 0 and path[0] == ".":
        path = path[1:]
    if len(path) > 0 and path[0] == "/":
        path = path[1:]

    if line_start < 0 or line_end < 0:
        raise ValueError("Line numbers must be non-negative")
    if line_start > line_end:
        raise ValueError("Line start must be less than or equal to line end")
    file = next((f for f in state.workspace if f.path.lower() == path.lower()), None)
    if not file:
        raise ValueError(f"File {path} not found")
    if settings.secretly_save:
        new_elements = get_overlaps(line_start, line_end, file)
        for element in new_elements:
            if (file.path, element.identifier) not in state.saved_elements: 
                state.saved_elements.append((file.path, element.identifier))
    content = file.updated_content
    if settings.unindent_inputs:
        content = unindent(content)
    if settings.number_lines:
        content = enumerate_lines(content)
    content = content.splitlines()
    if line_start >= len(content) or line_end >= len(content):
        raise ValueError("Line numbers out of range")
    lines = content[line_start:line_end+1]
    if len(lines) > settings.max_view_lines_end + settings.max_view_lines_start:
        lines = lines[:settings.max_view_lines_start] + ["..."] + lines[-settings.max_view_lines_end:] + ["\nNote: Showing only top and bottom " + str(settings.max_view_lines_start + settings.max_view_lines_end) + " lines to prevent context overflow."]
    return ("\n".join(lines), None, None)
    
def view_file_raw(state: AgentState, settings: ToolSettings, path: str):
    """
    View the contents of a file.
    
    Args:
        path: File path

    Returns:
        Formatted string showing:
        - The content of the file

    Example:
        View file src/auth/auth.py

    Tool Call:
        {"name": "view_file_raw", "arguments": {"path": "src/auth/auth.py"}}
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
    
    content = file.updated_content
    if settings.unindent_inputs:
        content = unindent(content)
    if settings.number_lines:
        content = enumerate_lines(content)
    lines = content.splitlines()
    if len(lines) > settings.max_view_lines_end + settings.max_view_lines_start:
        lines = lines[:settings.max_view_lines_start] + ["..."] + lines[-settings.max_view_lines_end:] + ["\nNote: Showing only top and bottom " + str(settings.max_view_lines_start + settings.max_view_lines_end) + " lines to prevent context overflow."]
    content = "\n".join(lines)
    return (content, None, None) 