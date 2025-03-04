import pytest
from agent2.formatting.autoformatter import find_shortest_indentation, unindent, reindent  # Replace with actual module name

print("hi")

# Test find_shortest_indentation
@pytest.mark.parametrize("input_text, expected", [
    # Uniform indentation
    ("   c\n    a\n  b", 2),
    # Mixed indentation with empty lines
    ("    line1    \n    line2\n  \n    line3", 4),
    # Whitespace-only lines
    ("\n\t\n\t\t", 0),  # All empty → 0
    # Tabs and spaces
    ("\tline1\n  line2", 1),  # Tab is considered 1 character
    # Zero indentation
    ("line1\nline2", 0),
])
def test_find_shortest_indentation(input_text, expected):
    print(input_text)
    assert find_shortest_indentation(input_text) == expected

# Test unindent
@pytest.mark.parametrize("input_text, expected", [
    # Standard case
    ("    def func():\n      pass", 
     "def func():\n  pass"""),
    
    # Preserve empty lines
    ("\tcontent\n\n\t\thi", "content\n\n\thi"),
    
    # Short lines handling
    (" short\n  longer", "short\n longer"),
    
    # Mixed whitespace
    ("\tline1\n  line2", 
     "line1\n line2")
])

def test_unindent(input_text, expected):
    assert unindent(input_text) == expected

# Test reindent
@pytest.mark.parametrize("original, new, expected", [
    ('  def original():\n      pass', 
     '    def new():\n        pass',
     '  def new():\n      pass'),
    
    ('def original():\n    pass', 
     '  def new():\n      pass',
     'def new():\n    pass'),
    
    ('\t\touter:\n\t\t\tinner', 
     '\tmodified:\n\t\t\t\timplementation\n\t\tpreserved',
     '\t\tmodified:\n\t\t\t\t\timplementation\n\t\t\tpreserved')
])
def test_reindent(original, new, expected):
    original_norm = original
    new_norm = new
    expected_norm = expected
    result = reindent(original_norm, new_norm)
    assert result == expected_norm, f"Expected:\n{expected_norm}\nGot:\n{result}"

# Edge Case Tests
def test_special_cases():
    # All empty input
    assert find_shortest_indentation("") == 0
    assert unindent("") == ""
    assert reindent("", "") == ""
    
    # New text shorter than original indent
    original = "    original"
    new = "new"
    assert reindent(original, new) == "    new"
    
    # Tabs in original text
    assert reindent("\toriginal", "new") == "\tnew"