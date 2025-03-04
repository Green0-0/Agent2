import pytest
from agent2.tools_common.element_tools.element_editing import replace_element_with, replace_element
from agent2.agent.agent_state import AgentState
from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.element import Element
from typing import List

# Fixtures
@pytest.fixture
def sample_file_with_elements():
    elements = [
        Element("func1", "def func1():\n    pass", "Function 1", 0, None, []),
        Element("func2", "def func2():\n    return 42", "Function 2", 2, None, []),
    ]
    return File("test.py", "def func1():\n    pass\ndef func2():\n    return 42")

@pytest.fixture
def agent_state_with_elements(sample_file_with_elements):
    return AgentState(None, [sample_file_with_elements])

@pytest.fixture
def tool_settings():
    return ToolSettings()

# Tests for replace_element_with
def test_replace_element_with_single_element(agent_state_with_elements, tool_settings):
    replace_element_with(agent_state_with_elements, tool_settings, "test.py", "func1", "def func1():\n    return 0")
    updated = agent_state_with_elements.workspace[0].updated_content.splitlines()
    assert updated == ["def func1():", "    return 0", "def func2():", "    return 42"]

def test_replace_element_with_multiple_lines(agent_state_with_elements, tool_settings):
    replace_element_with(agent_state_with_elements, tool_settings, "test.py", "func2", "def func2():\n    return 100\n    # New comment")
    updated = agent_state_with_elements.workspace[0].updated_content.splitlines()
    assert updated == ["def func1():", "    pass", "def func2():", "    return 100", "    # New comment"]

def test_replace_element_with_element_not_found(agent_state_with_elements, tool_settings):
    with pytest.raises(ValueError, match="Element not_found not found in file test.py"):
        replace_element_with(agent_state_with_elements, tool_settings, "test.py", "not_found", "def not_found():\n    pass")

def test_replace_element_with_no_changes(agent_state_with_elements, tool_settings):
    with pytest.raises(ValueError, match="No changes made!"):
        replace_element_with(agent_state_with_elements, tool_settings, "test.py", "func1", "def func1():\n    pass")

def test_replace_element_with_reindent_enabled(agent_state_with_elements, tool_settings):
    tool_settings.reindent_outputs = True
    replace_element_with(agent_state_with_elements, tool_settings, "test.py", "func1", "  def func1():\n      return 0")
    updated = agent_state_with_elements.workspace[0].updated_content.splitlines()
    assert updated == ["def func1():", "    return 0", "def func2():", "    return 42"]

def test_replace_element_with_path_normalization(agent_state_with_elements, tool_settings):
    replace_element_with(agent_state_with_elements, tool_settings, "./test.py", "func1", "def func1():\n    return 0")
    updated = agent_state_with_elements.workspace[0].updated_content.splitlines()
    assert updated == ["def func1():", "    return 0", "def func2():", "    return 42"]

# Tests for replace_element
def test_replace_element_using_last_code_block(agent_state_with_elements, tool_settings):
    agent_state_with_elements.last_code_block = "def func1():\n    return 0"
    replace_element(agent_state_with_elements, tool_settings, "test.py", "func1")
    updated = agent_state_with_elements.workspace[0].updated_content.splitlines()
    assert updated == ["def func1():", "    return 0", "def func2():", "    return 42"]

def test_replace_element_no_last_code_block(agent_state_with_elements, tool_settings):
    agent_state_with_elements.last_code_block = None
    with pytest.raises(ValueError, match="No previous code block found!"):
        replace_element(agent_state_with_elements, tool_settings, "test.py", "func1")

# Utility tests
def test_diff_generation_with_elements(agent_state_with_elements, tool_settings):
    replace_element_with(agent_state_with_elements, tool_settings, "test.py", "func1", "def func1():\n    return 0")
    diff = agent_state_with_elements.workspace[0].diff(None)
    assert "-    pass" in diff and "+    return 0" in diff

def test_path_normalization_in_functions_with_elements(agent_state_with_elements, tool_settings):
    replace_element_with(agent_state_with_elements, tool_settings, "./test.py", "func1", "def func1():\n    return 0")
    updated = agent_state_with_elements.workspace[0].updated_content.splitlines()
    assert updated == ["def func1():", "    return 0", "def func2():", "    return 42"]