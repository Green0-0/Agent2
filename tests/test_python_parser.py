import pytest
from agent2.formatting.parsers.parse_python import parse_python_elements
from agent2.element import Element

def find_element_by_identifier(elements: list[Element], target_id: str) -> Element | None:
    """Helper to find element by identifier in nested structure"""
    for elem in elements:
        if elem.identifier == target_id:
            return elem
        if found := find_element_by_identifier(elem.elements, target_id):
            return found
    return None

def test_empty_code():
    """Test empty input returns empty list"""
    assert parse_python_elements("") == []

def test_single_function():
    """Test single top-level function"""
    code = "def myfunc():\n\tpass"
    elements = parse_python_elements(code)
    assert len(elements) == 1
    assert elements[0].identifier == "myfunc"
    assert elements[0].line_start == 0
    assert not elements[0].elements

def test_class_with_method():
    """Test class containing a method"""
    code = "class MyClass:\n\tdef method(self):\n\t\tpass"
    elements = parse_python_elements(code)
    cls = find_element_by_identifier(elements, "MyClass")
    method = find_element_by_identifier(elements, "MyClass.method")
    
    assert cls is not None
    assert method is not None
    assert method.line_start == 1

def test_function_with_decorator():
    """Test decorator affects line_start calculation"""
    code = "@decorator\ndef myfunc():\n\tpass"
    elements = parse_python_elements(code)
    print(elements)
    assert elements[0].line_start == 0

def test_multiple_decorators():
    """Test multiple decorators use highest line number"""
    code = "@decorator1\n@decorator2\ndef myfunc():\n\tpass"
    elements = parse_python_elements(code)
    print(elements)
    assert elements[0].line_start == 0

def test_docstrings():
    """Test docstring extraction"""
    code = 'def func():\n\t"""Function docstring"""\n\tpass\n\nclass MyClass:\n\t"""Class docstring"""\n\tdef method(self):\n\t\t"""Method docstring"""\n\t\tpass'
    elements = parse_python_elements(code)
    assert find_element_by_identifier(elements, "func").description.strip() == '"""Function docstring"""'
    assert find_element_by_identifier(elements, "MyClass").description.strip() == '"""Class docstring"""'
    assert find_element_by_identifier(elements, "MyClass.method").description.strip() == '"""Method docstring"""'

def test_nested_elements():
    """Test nested function hierarchy"""
    code = "def outer():\n\tdef inner():\n\t\tpass"
    elements = parse_python_elements(code)
    outer = find_element_by_identifier(elements, "outer")
    inner = find_element_by_identifier(elements, "outer.inner")
    
    assert outer is not None
    assert inner is not None
    assert inner.line_start == 1

def test_multiple_top_level_elements():
    """Test mixed top-level elements"""
    code = "def func1():\n\tpass\n\nclass Class1:\n\tpass\n\ndef func2():\n\tpass"
    elements = parse_python_elements(code)
    ids = {e.identifier for e in elements}
    assert ids == {"func1", "Class1", "func2"}

def test_complex_hierarchy():
    """Test complex nested structure from example"""
    code = "class thing:\n\tdef method1():\n\t\t@header\n\t\tdef method2():\n\t\t\t\"\"\"\n\t\t\tdocstring for method2\n\t\t\t\"\"\"\n\t\t\tpass\n\t\tpass\n\tdef init():\n\t\tpass\n\ndef method3():\n\tpass"
    elements = parse_python_elements(code)
    print(elements)
    # Check top level elements
    assert len(elements) == 2
    assert {e.identifier for e in elements} == {"thing", "method3"}
    
    # Check class hierarchy
    thing = find_element_by_identifier(elements, "thing")
    method1 = find_element_by_identifier(elements, "thing.method1")
    method2 = find_element_by_identifier(elements, "thing.method1.method2")
    init = find_element_by_identifier(elements, "thing.init")
    
    assert thing is not None
    assert method1 is not None
    assert method2 is not None
    assert init is not None
    
    # Verify line starts
    assert method1.line_start == 1
    assert method2.line_start == 2
    assert "docstring for method2" in method2.description
    assert init.line_start == 9  # Line with "def init():" in 0-based numbering