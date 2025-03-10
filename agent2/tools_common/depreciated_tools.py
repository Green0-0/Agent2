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
