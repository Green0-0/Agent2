from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState
from agent2.formatting.autoformatter import reindent, unenumerate_lines, remove_codeblock

def replace_element_with(state: AgentState, settings: ToolSettings, path: str, identifier: str, replacement: str):
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
        {"name": "replace_element_with", "arguments": {"path": "src/auth/auth.py", "identifier": "auth", "replacement": "def auth():\\n\\tpass"}}
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
    if removed_line_numbers[0] > 0.9 * len(removed_line_numbers[2]):
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
    if original_chunk == new_chunk:
        raise ValueError("No changes made!")
    
    lines[line_start:line_end] = new_chunk.splitlines()
    new_content = "\n".join(lines)
    file.updated_content = new_content
    file.update_elements()
    return "Success:\n" + file.diff(None)


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