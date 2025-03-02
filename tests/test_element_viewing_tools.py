import pytest
from agent2.element import Element
from agent2.tools_common.element_tools.element_viewing import search_elements, view_element
from agent2.agent.tool_settings import ToolSettings
from agent2.file import File
from agent2.agent.agent_state import AgentState

# Fixtures
@pytest.fixture
def mock_settings():
    settings = ToolSettings()
    settings.max_search_result_listings = 5
    settings.max_search_result_lines = 10
    return settings

@pytest.fixture
def sample_file():
    content = """0: class MyClass:
1:     '''Class docstring'''
2:     def method1(self):
3:         print("hello")
4:     
5:     def method2(self):
6:         '''Method doc'''
7:         print("world")
8:         if True:
9:             print("nested")
10: """
    file = File("test.py", content)
    file.elements = [
        Element(
            identifier="MyClass",
            content="class MyClass:\n    '''Class docstring'''\n    def method1...",
            description="Class docstring",
            line_start=0,
            embedding=None,
            elements=[
                Element(
                    identifier="MyClass.method1",
                    content="def method1(self):\n    print('hello')",
                    description="",
                    line_start=2,
                    embedding=None,
                    elements=[]
                ),
                Element(
                    identifier="MyClass.method2",
                    content="def method2(self):\n    '''Method doc'''\n    print('world')\n    if True:\n        print('nested')",
                    description="Method doc",
                    line_start=5,
                    embedding=None,
                    elements=[]
                )
            ]
        )
    ]
    return file

# Element Tests
def test_element_str_basic():
    element = Element(
        identifier="test",
        content="def foo():\n    print(1)\n    print(2)",
        description="test func",
        line_start=10,
        embedding=None,
        elements=[]
    )
    assert element.to_string(number_lines=False) == "def foo():\n    print(1)\n    print(2)"

def test_element_str_with_subelements():
    element = Element(
        identifier="parent",
        content="class Parent:\n    def child1():\n        pass\n    def child2():\n        pass",
        description="",
        line_start=5,
        embedding=None,
        elements=[
            Element("child1", "def child1():\n    pass", "", 6, None, []),
            Element("child2", "def child2():\n    pass", "", 8, None, [])
        ]
    )
    assert element.to_string() == """5 class Parent:
6     def child1():...
8     def child2():..."""

def test_to_string():
    element = Element(
        identifier="lined",
        content="a\nb\nc",
        description="",
        line_start=10,
        embedding=None,
        elements=[]
    )
    assert element.to_string() == "10 a\n11 b\n12 c"

# search_elements Tests
def test_search_elements_basic(mock_settings, sample_file):
    state = AgentState(None, [sample_file])
    results = search_elements(state, mock_settings, r"print\(")
    
    assert "MyClass.method1: 1 matches" in results
    assert "MyClass.method2: 2 matches" in results
    assert "Method doc" in results
    assert "print('hello')" in results
    assert "print('world')" in results

def test_search_extensions_filter(mock_settings):
    py_file = File("test.py", "def what():\n\tpass")
    js_file = File("test.java", "class myClass:\n\tvoid what():\n\t\treturn")
    state = AgentState(None, [py_file, js_file])
    print(py_file.elements)
    
    results = search_elements(state, mock_settings, ".", "test", extensions="py")
    assert "test.py" in results
    assert "test.js" not in results

def test_search_path_filter(mock_settings):
    root_file = File("src/test.py", "def what():\n\tpass")
    nested_file = File("src/utils/test.py", "def what():\n\tpass") 
    state = AgentState(None, [root_file, nested_file])
    
    results = search_elements(state, mock_settings, ".", path="src/utils")
    assert "src/utils/test.py" in results
    assert "src/test.py" not in results

def test_search_invalid_regex(mock_settings, sample_file):
    state = AgentState(None, [sample_file])
    with pytest.raises(ValueError):
        search_elements(state, mock_settings, r"print([")

# view_element Tests
def test_view_element_found(mock_settings, sample_file):
    state = AgentState(None, [sample_file])
    result = view_element(state, mock_settings, "test.py", "MyClass.method2")
    assert result == """5 def method2(self):
6     '''Method doc'''
7     print('world')
8     if True:
9         print('nested')"""

def test_view_element_not_found(mock_settings, sample_file):
    state = AgentState(None, [sample_file])
    with pytest.raises(ValueError):
        view_element(state, mock_settings, "test.py", "NonExistent")

# Edge Cases
def test_empty_element():
    element = Element("empty", "", "desc", 0, None, [])
    assert element.to_string(number_lines=False) == ""
    assert element.to_string() == "0 "

def test_element_at_file_end():
    element = Element("end", "last_line", "", 99, None, [])
    assert element.to_string() == "99 last_line"

# Tool Settings Limits
def test_search_result_limiting(mock_settings):
    mock_settings.max_search_result_listings = 2
    mock_settings.max_search_result_lines = 3
    
    elements = [Element(f"elem{i}", f"match {i}", "", i, None, []) for i in range(5)]
    files = [File("test.py", "") for _ in range(5)]
    for f in files:
        f.elements = elements
        
    state = AgentState(None, files)
    results = search_elements(state, mock_settings, "match")
    
    assert "Showing top 2/25 matches" in results