from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.element import Element
from agent2.agent.agent_state import AgentState
from typing import List

def normalize_path(path: str):
    """Normalize file path by replacing backslashes and removing leading dots/slashes."""
    if "\\" in path:
        path = path.replace("\\", "/")
    if path.startswith("."):
        path = path[1:]
    if path.startswith("/"):
        path = path[1:]
    return path

def find_file(state: AgentState, path: str):
    """Find a file in the workspace by its normalized path."""
    path = normalize_path(path)
    file = next((f for f in state.workspace if f.path.lower() == path.lower()), None)
    if not file:
        raise ValueError(f"File {path} not found")
    return file

def truncate_lines(settings: ToolSettings, lines: List[str]):
    """Truncate lines if they exceed the maximum view limits."""
    if len(lines) > settings.max_view_lines_start + settings.max_view_lines_end:
        return (
            lines[:settings.max_view_lines_start] + 
            ["..."] + 
            lines[-settings.max_view_lines_end:],
            f"\nNote: Showing only top and bottom {settings.max_view_lines_start + settings.max_view_lines_end} lines to prevent context overflow."
        )
    return (lines, "")