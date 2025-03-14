import pytest
from agent2.tools_common.basic_tools.basic_editing import replace_lines_with, replace_lines, replace_block, replace_block_with
from agent2.agent.agent_state import AgentState
from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from typing import List

# Fixtures
@pytest.fixture
def sample_file():
    return File("test.txt", "line0\nline1\nline2\nline3\nline4")

@pytest.fixture
def agent_state(sample_file):
    return AgentState(None, [sample_file])

@pytest.fixture
def tool_settings():
    return ToolSettings()

# Tests for replace_lines_with
def test_replace_lines_with_single_line(agent_state, tool_settings):
    replace_lines_with(agent_state, tool_settings, "test.txt", 2, 2, "new_line2")
    updated = agent_state.workspace[0].updated_content.splitlines()
    assert updated == ["line0", "line1", "new_line2", "line3", "line4"]

def test_replace_lines_with_multiple_lines(agent_state, tool_settings):
    replace_lines_with(agent_state, tool_settings, "test.txt", 1, 3, "new_line1\nnew_line2\nnew_line3")
    updated = agent_state.workspace[0].updated_content.splitlines()
    assert updated == ["line0", "new_line1", "new_line2", "new_line3", "line4"]

def test_replace_lines_with_out_of_range(agent_state, tool_settings):
    with pytest.raises(ValueError, match="Line numbers out of range"):
        replace_lines_with(agent_state, tool_settings, "test.txt", 5, 5, "hi")

def test_replace_lines_start_gt_end(agent_state, tool_settings):
    with pytest.raises(ValueError, match="Line start must be less than or equal to line end"):
        replace_lines_with(agent_state, tool_settings, "test.txt", 3, 2, "hi")

def test_replace_lines_no_changes(agent_state, tool_settings):
    file = agent_state.workspace[0]
    original_line = file.updated_content.splitlines()[2]
    with pytest.raises(ValueError, match="No changes made!"):
        replace_lines_with(agent_state, tool_settings, "test.txt", 2, 2, original_line)

def test_replace_lines_reindent_enabled(agent_state, tool_settings):
    file = File("test.py", "def foo():\n    pass")
    agent_state.workspace = [file]
    tool_settings.reindent_outputs = True
    replace_lines_with(agent_state, tool_settings, "test.py", 1, 1, "return True")
    assert file.content == "def foo():\n    return True"

def test_replace_lines_path_normalization(agent_state, tool_settings):
    file = agent_state.workspace[0]
    replace_lines_with(agent_state, tool_settings, ".\\test.txt", 0, 0, "new_line0")
    assert file.updated_content.splitlines()[0] == "new_line0"

# Tests for replace_block_with
def test_replace_block_with_single_line(agent_state, tool_settings):
    file = File("test.py", "def foo():\n    pass")
    agent_state.workspace = [file]
    replace_block_with(agent_state, tool_settings, "test.py", "def foo():", "def foo(param):")
    assert file.content.splitlines()[0] == "def foo(param):"

def test_replace_block_with_multi_line():
    file = File("test.py", "def foo():\n    pass")
    state = AgentState(None, [file])
    settings = ToolSettings()
    replace_block_with(state, settings, "test.py", "def foo():\n    pass", "def bar():\n    return")
    assert file.content == "def bar():\n    return"

def test_replace_block_with_not_found(agent_state, tool_settings):
    with pytest.raises(ValueError, match="Block not found"):
        replace_block_with(agent_state, tool_settings, "test.txt", "invalid_block", "replacement")

# Tests for replace_lines
def test_replace_lines_using_last_code_block(agent_state, tool_settings):
    agent_state.last_code_block = "new_line1"
    replace_lines(agent_state, tool_settings, "test.txt", 1, 1)
    assert agent_state.workspace[0].updated_content.splitlines()[1] == "new_line1"

def test_replace_lines_no_last_code_block(agent_state, tool_settings):
    agent_state.last_code_block = None
    with pytest.raises(ValueError, match="No previous code block found!"):
        replace_lines(agent_state, tool_settings, "test.txt", 0, 0)

# Tests for replace_block
def test_replace_block_using_last_code_block():
    file = File("test.py", "def foo():")
    state = AgentState(None, [file])
    state.last_code_block = "def foo(param):"
    replace_block(state, ToolSettings(), "test.py", "def foo():")
    assert file.content == "def foo(param):"

def test_replace_block_no_last_code_block(agent_state, tool_settings):
    agent_state.last_code_block = None
    with pytest.raises(ValueError, match="No previous code block found!"):
        replace_block(agent_state, tool_settings, "test.txt", "block")

# Utility tests
def test_diff_generation():
    original = "line1\nline2\nline3"
    updated = "line1\nmodified\nline3"
    file = File("test.txt", original)
    file.content = updated
    diff = file.diff(None)
    assert "modified" in diff and "line2" in diff

def test_path_normalization_in_functions(agent_state, tool_settings):
    file = File("test.txt", "content")
    agent_state.workspace = [file]
    replace_lines_with(agent_state, tool_settings, "./test.txt", 0, 0, "new_content")
    assert file.content == "new_content"