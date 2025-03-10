from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState
from agent2.formatting.autoformatter import reindent, remove_codeblock, unenumerate_lines
from agent2.formatting.lookup import lookup_text
import re

def replace_lines(state: AgentState, settings: ToolSettings, path: str, line_start: int, line_end: int, replacement: str):
    """
    Replace lines in a file with a replacement string. Make sure to include all the lines that need to be removed and substituted with the replacement code, which must be written in its entirety.
    
    Args:
        path: File path
        line_start: Starting line number, inclusive
        line_end: Ending line number, inclusive
        replacement: String to replace lines with
    
    Returns:
        Diff of the file, or failure

    Example:
        Replace lines 100-100 (line 100) of auth.py with ``i = 5``
    Tool Call:
        {"name": "replace_lines", "arguments": {"path": "src/auth/auth.py", "line_start": 100, "line_end": 100, "replacement": "i = 5"}}
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
    file = next((f for f in state.workspace if f.path == path), None)
    if not file:
        raise ValueError(f"File {path} not found")
    removed_line_numbers = unenumerate_lines(replacement)
    if removed_line_numbers[0] > 0.6 * len(removed_line_numbers[1]):
        replacement = removed_line_numbers[2]
    replacement = remove_codeblock(replacement)
    content = file.updated_content
    lines = content.splitlines()
    if line_start >= len(lines) or line_end >= len(lines):
        raise ValueError("Line numbers out of range")
    original_chunk = "\n".join(lines[line_start:line_end+1])
    if settings.reindent_outputs:
        new_chunk = reindent(original_chunk, replacement)
    else:
        new_chunk = replacement
    if lookup_text(original_chunk, new_chunk, settings.match_strict_level) == 0:
        raise ValueError("No changes made!")
    
    lines[line_start:line_end+1] = new_chunk.splitlines()
    new_content = "\n".join(lines)
    file.updated_content = new_content
    
    file.update_elements()
    return ("Success:\n" + file.diff(None), None, None)

def replace_block(state: AgentState, settings: ToolSettings, path: str, block: str, replacement: str):
    """
    Replace a block in a file with a replacement string. You must output the entire block being replaced, and every line that must be deleted, which must be written in its entirety.
    
    Args:
        path: File path
        block: Block to replace, every line must be typed in its entirety and matched exactly
        replacement: String to replace block with
    
    Returns:
        Diff of the file, or failure

    Example:
        Replace block ```\ndef login():\n    i = 5\n``` in auth.py with ```\ndef login(username, password):\n    i = 6\n```
    Tool Call:
        {"name": "replace_block", "arguments": {"path": "src/auth/auth.py", "block": "def login():\\n    i = 5", "replacement": "def login(username, password):\\n    i = 6"}}
    """
    if "\\" in path:
        path = path.replace("\\", "/")
    if len(path) > 0 and path[0] == ".":
        path = path[1:]
    if len(path) > 0 and path[0] == "/":
        path = path[1:]

    file = next((f for f in state.workspace if f.path == path), None)
    if not file:
        raise ValueError(f"File {path} not found")
    
    block_start_line = lookup_text(file.updated_content, block, strict_level=settings.match_strict_level)
    block_end_line = block_start_line + len(block.split("\n")) - 1

    if block_start_line < 0 or block_end_line < 0:
        raise ValueError("Block not found")
    
    if block_start_line > block_end_line:
        raise ValueError("This is an extremely strange error that should not occur: Block start must be less than or equal to block end!")
    
    return replace_lines(state, settings, path, block_start_line, block_end_line, replacement)