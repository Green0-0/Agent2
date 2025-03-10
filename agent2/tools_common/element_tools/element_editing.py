import functools
from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.element import Element
from agent2.agent.agent_state import AgentState
from agent2.formatting.autoformatter import reindent, unenumerate_lines, remove_codeblock, enumerate_lines, unindent
from agent2.formatting.lookup import lookup_text

def replace_element(state: AgentState, settings: ToolSettings, path: str, identifier: str, replacement: str):
    """
    Replace an element and all its subelements with a replacement string. Always edit the innermost elements and not outer elements. Replace one element at a time. Make sure to specify the element path exactly, and the entirety of the replacement code, otherwise it will be cut off; if you want to view the bar method within the foo class, use foo.bar.
    
    Args:
        path: File path
        identifier: Identifier of the element to replace
        replacement: String to replace lines with
    
    Returns:
        Diff of the file, or failure

    Example:
        Replace element auth in auth.py with ```python\ndef auth():\n\tpass\n```
    Tool Call:
        {"name": "replace_element", "arguments": {"path": "src/auth/auth.py", "identifier": "auth", "replacement": "def auth():\\n\\tpass"}}
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
        # Find closest element
        element = next((e for e in all_elements if identifier.lower() in e.identifier.lower()), None)
        if not element:
            element = next((e for e in all_elements if identifier.lower().split(".")[-1] in e.identifier.lower()), None)
        if not element:
            element = next((e for e in all_elements if e.identifier.lower().split(".")[-1] in identifier.lower()), None)
        if not element:
            raise ValueError(f"Element {identifier} not found in file {path}")
        else:
            raise ValueError(f"Element {identifier} not found in file {path}. Did you mean {element.identifier}?")
    
    line_start = element.line_start
    line_end = line_start + len(element.content.splitlines())

    removed_line_numbers = unenumerate_lines(replacement)
    if removed_line_numbers[0] > 0.6 * len(removed_line_numbers[1]):
        replacement = removed_line_numbers[2]
    replacement = remove_codeblock(replacement)

    content = file.updated_content
    lines = content.splitlines()
    if line_start > len(lines) or line_end > len(lines) or line_start > line_end:
        raise ValueError("This is an extremely strange error that should not occur: Element numbers out of range")
    
    original_chunk = "\n".join(lines[line_start:line_end])
    if settings.reindent_outputs:
        new_chunk = reindent(original_chunk, replacement)
    else:
        new_chunk = replacement
    if lookup_text(original_chunk, new_chunk, settings.match_strict_level) == 0:
        raise ValueError("No changes made!")
    
    lines[line_start:line_end] = new_chunk.splitlines()
    new_content = "\n".join(lines)
    file.updated_content = new_content
    file.update_elements()
    return ("Success:\n" + file.diff(None), None, None)

def open_element(state: AgentState, settings: ToolSettings, path: str, identifier: str):
    """
    Open up an element, will allow you to edit that element. Always prioritize opening inner functions and not outer classes and functions. Make sure to specify the element path exactly; if you want to view the bar method within the foo class, use foo.bar. After editing, the file will be closed and any diffs (from editing) will be shown.
    
    Args:
        path: File path
        identifier: Element identifier to view
    
    Returns:
        Diffs from editing (after the file is closed)

    Example:
        Open element auth and prepare to edit it
    Tool Call:
        {"name": "open_element", "arguments": {"path": "src/auth/auth.py", "identifier": "auth"}}
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
        # Find closest element
        element = next((e for e in all_elements if identifier.lower() in e.identifier.lower()), None)
        if not element:
            element = next((e for e in all_elements if identifier.lower().split(".")[-1] in e.identifier.lower()), None)
        if not element:
            element = next((e for e in all_elements if e.identifier.lower().split(".")[-1] in identifier.lower()), None)
        if not element:
            raise ValueError(f"Element {identifier} not found in file {path}")
        else:
            raise ValueError(f"Element {identifier} not found in file {path}. Did you mean {element.identifier}?")
    if len(element.content.splitlines()) > 600:
        raise ValueError("This element is way too large to directly edit!")
    if settings.secretly_save:
        if (file.path, element.identifier) not in state.saved_elements:
            state.saved_elements.append((file.path, element.identifier))
    partial_open_element = functools.partial(open_element_final, state, settings, path, identifier)
    return (f"```python\n{element.to_string(unindent_text = settings.unindent_inputs, number_lines = settings.number_lines, mask_subelements = False)}\n```\nIf you would like to make any changes, output a replacement code block, wrapped within ``` for the entirety of this element. You do not need to use any tool calls for this operation, nor do you need to include line numbers in the code you write. If you would like to cancel, do not output a code block and instead output a cancellation reason.", None, partial_open_element)
        
def open_element_final(state: AgentState, settings: ToolSettings, path: str, identifier: str, input: str):
    """
    Close the file and parse any edits
    """
    state.chat.messages.pop()

    if input.count("```") < 2:
        return ("No edits made with message:\n" + input + "\nNote that edits made within open_element need to be wrapped inside code blocks.", None, None)

    last_closing = input.rfind('```')
    # Find the opening triple backticks before the last closing
    opening_start = input.rfind('```', 0, last_closing)
    if opening_start == -1:
        return ("No edits made with message:\n" + input + "\nNote that edits made within open_element need to be wrapped inside code blocks.", None, None)
    newline_pos = input.find('\n', opening_start)
    if newline_pos == -1:
        newline_pos = input.find(' ', opening_start) + 1
    else:
        code_start = newline_pos + 1
    
    # Parse input, check if code block is contained, pop last chat message
    return replace_element(state, settings, path, identifier, input[code_start:last_closing])

def open_element_at(state: AgentState, settings: ToolSettings, path: str, line: int):
    """
    Open the innermost element at a specific line in a file for editing. The line is zero-indexed. This tool finds the deepest nested element at the given line and calls open_element for it.
    
    Args:
        path: Path to the file
        line: Zero-indexed line number in the file
    
    Returns:
        The output of open_element for the found element
    
    Example:
        Open element at line 5 in src/app.py
    Tool Call:
        {"name": "open_element_at", "arguments": {"path": "src/app.py", "line": 5}}
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
    
    # Call open_element with the found identifier
    return open_element(state, settings, path, best_element.identifier)

def replace_element_at(state: AgentState, settings: ToolSettings, path: str, line: int, replacement: str):
    """
    Replace the innermost element at a specific line in a file. The line is zero-indexed. This tool finds the deepest nested element at the given line and calls replace_element for it.
    
    Args:
        path: Path to the file
        line: Zero-indexed line number in the file
        replacement: Replacement code for the element
    
    Returns:
        The output of replace_element for the found element
    
    Example:
        Replace element at line 5 in src/app.py with new code
    Tool Call:
        {"name": "replace_element_at", "arguments": {"path": "src/app.py", "line": 5, "replacement": "def new_func():\\n    pass"}}
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
    
    # Call replace_element with the found identifier and replacement
    return replace_element(state, settings, path, best_element.identifier, replacement)