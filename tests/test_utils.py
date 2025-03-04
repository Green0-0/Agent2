import pytest
from agent2.file import File
from agent2.utils.utils import get_overlaps

def create_test_file(content):
    """Helper to create a File with parsed elements from content"""
    file = File(path="test.py", content=content)
    return file

def get_identifiers(elements):
    """Get sorted list of element identifiers for easier comparison"""
    return sorted([e.identifier for e in elements])

def test_nested_selection():
    content = """
def nested():
    def nested2():
        def nested4():
            pass
""".strip()
    file = create_test_file(content)
    
    # Test line 3-4 (0-based, content lines are 0:def nested, 1:def nested2, 2:def nested4, 3:pass)
    result = get_overlaps(2, 3, file)
    assert get_identifiers(result) == sorted(["nested", "nested.nested2", "nested.nested2.nested4"])

def test_parent_child_overlap():
    content = """class thing:
    def method1():
        pass
    def method2():
        pass
""".strip()
    file = create_test_file(content)
    
    # Lines 1-2 should capture both class and methods
    result = get_overlaps(1, 2, file)
    assert get_identifiers(result) == sorted(["thing", "thing.method1"])

def test_single_line_selection():
    content = """
def nested():
    def nested2():
        pass
""".strip()
    file = create_test_file(content)
    
    # Line 1 (def nested2) should capture both parent and child
    result = get_overlaps(1, 1, file)
    assert get_identifiers(result) == sorted(["nested", "nested.nested2"])

def test_deep_exception_case():
    content = """
class longmethodholder:
    def longmethod():
        # 4 lines of implementation
        1+1
        1+2
        2+3
        pass
""".strip()
    file = create_test_file(content)
    
    # Select implementation lines (2-5)
    result = get_overlaps(2, 5, file)
    assert get_identifiers(result) == ["longmethodholder.longmethod"]

def test_boundary_condition():
    content = """
class secondclass:
    pass
""".strip()
    file = create_test_file(content)
    
    # Entire class selection
    result = get_overlaps(0, 1, file)
    assert get_identifiers(result) == ["secondclass"]

def test_partial_overlap():
    content = """
def outer():
    def middle():
        def inner():
            pass
""".strip()
    file = create_test_file(content)
    
    # Select middle's definition line
    result = get_overlaps(1, 1, file)
    assert get_identifiers(result) == sorted(["outer", "outer.middle"])