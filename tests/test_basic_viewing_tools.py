import pytest
from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState
from agent2.tools_common.basic_tools.basic_viewing import search_files, view_lines

@pytest.fixture
def sample_files():
    return [
        File(
            path="src/auth/auth.py",
            content="def authenticate():\n    # Auth logic here\n    print('LOGIN_SUCCESS')"
        ),
        File(
            path="src/utils/network.py",
            content="def connect():\n    # Session management\n    token = 'temp_session'\n    return token"
        ),
        File(
            path="README.md",
            content="Project Documentation\nAuthentication Details"
        )
    ]

@pytest.fixture
def agent_state(sample_files):
    return AgentState(chat=None, files=sample_files)

@pytest.fixture
def tool_settings():
    settings = ToolSettings()
    settings.max_search_result_listings = 3
    settings.max_search_result_lines = 10
    return settings

# Search Files Tests
def test_search_valid_regex(agent_state, tool_settings):
    result = search_files(agent_state, tool_settings, 
                         regex="auth|session", path=".")
    assert "src/auth/auth.py" in result
    assert "3 matches" in result
    assert "def authenticate()" in result
    assert "# Auth logic here" in result

def test_search_invalid_regex(agent_state, tool_settings):
    with pytest.raises(ValueError):
        search_files(agent_state, tool_settings, regex="(unclosed", path="")

def test_search_extension_filter(agent_state, tool_settings):
    result = search_files(agent_state, tool_settings,
                        regex="session", extensions="py")
    assert "src/utils/network.py" in result
    assert "README.md" not in result

def test_search_case_insensitive(agent_state, tool_settings):
    result = search_files(agent_state, tool_settings, regex="LOGIN")
    assert "LOGIN_SUCCESS" in result

def test_search_path_normalization(agent_state, tool_settings):
    result1 = search_files(agent_state, tool_settings, 
                          regex="auth", path="./src/")
    result2 = search_files(agent_state, tool_settings,
                          regex="auth", path="src/")
    assert result1 == result2

def test_search_result_limiting(agent_state, tool_settings):
    tool_settings.max_search_result_listings = 1
    tool_settings.max_search_result_lines = 4
    result = search_files(agent_state, tool_settings, regex="auth|session")
    assert "Showing top 1/3 matches" in result
    assert result.count('\n') <= tool_settings.max_search_result_lines + 1

# View Lines Tests
def test_view_valid_range(agent_state, tool_settings):
    result = view_lines(agent_state, tool_settings, 
                       line_start=0, line_end=1, path="src/auth/auth.py")
    assert "def authenticate()" in result
    assert "# Auth logic here" in result

def test_view_line_numbering(agent_state, tool_settings):
    tool_settings.number_lines = True
    result = view_lines(agent_state, tool_settings,
                       line_start=0, line_end=0, path="src/auth/auth.py")
    assert "0 def authenticate()" in result

def test_view_unindent(agent_state, tool_settings):
    tool_settings.unindent_inputs = True
    file = File(path="test.py", content="    indented line")
    state = AgentState(chat=None, files=[file])
    result = view_lines(state, tool_settings, 0, 0, "test.py")
    assert "indented line" in result

def test_view_truncation(agent_state, tool_settings):
    tool_settings.max_view_lines_start = 2
    tool_settings.max_view_lines_end = 1
    content = "\n".join(f"Line {i}" for i in range(200))
    file = File(path="long.py", content=content)
    state = AgentState(chat=None, files=[file])
    result = view_lines(state, tool_settings, 0, 199, "long.py")
    assert "Line 0" in result
    assert "Line 199" in result
    assert "..." in result
    assert "context overflow" in result

def test_view_invalid_range(agent_state, tool_settings):
    with pytest.raises(ValueError):
        view_lines(agent_state, tool_settings, 10, 5, "src/auth/auth.py")

def test_view_file_not_found(agent_state, tool_settings):
    with pytest.raises(ValueError):
        view_lines(agent_state, tool_settings, 0, 1, "missing.txt")