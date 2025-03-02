import pytest
from agent2.formatting.lookup import lookup_text

# Original example from problem description
def test_example_provided():
    search_block = """def thing1:
  print("Thinkg")
class myclass:
  def init():
    pass
  def method():
    pass"""
    search_for = """class myclass:
  def init():
    pass"""
    assert lookup_text(search_block, search_for, 3) == 2

# Strict Level 4 Tests
def test_strict4_exact_match_ignore_empty_lines():
    assert lookup_text("a\n\nb\nc", "a\nb\nc", 4) == 0

def test_strict4_search_for_has_more_empty_lines():
    assert lookup_text("a\nb\nc", "a\n\n\nb\n\nc", 4) == 0

def test_strict4_no_match():
    assert lookup_text("a\nb\nc", "x\ny\nz", 4) == -1

def test_strict4_match_with_empty_lines_in_block():
    assert lookup_text("start\n\nmiddle\n\nend", "middle\nend", 4) == 2

# Strict Level 3 Tests
def test_strict3_unindented_match():
    search_block = "\t\tclass myclass:\n\t\t\tdef init():\n\t\t\t\tpass"
    search_for = "class myclass:\n\tdef init():\n\t\tpass"
    assert lookup_text(search_block, search_for, 3) == 0

def test_strict3_consecutive_lines_after_unindent():
    assert lookup_text("    line1\n    line2\n\n    line3", 
                      "line2\nline3", 3) == 1

def test_strict3_varying_indentation_with_unindent():
    search_block = """\t\t\t\tdef outer():\n\t\tclass Inner:\n\t\t\tdef method():\n\t\t\t\tpass"""
    search_for = "class Inner:\n\tdef method():"
    assert lookup_text(search_block, search_for, 3) == 1

def test_strict3_no_match_due_to_ordering():
    assert lookup_text("a\nb\nc", "c\nb", 3) == -1

# Strict Level 2 Tests
def test_strict2_stripped_lines():
    assert lookup_text("  a  \n  b  \n  c  ", "a\nb\nc", 2) == 0

def test_strict2_leading_trailing_spaces():
    assert lookup_text("   hello   \n   world   ", "hello\nworld", 2) == 0

def test_strict2_whitespace_only_lines_ignored():
    assert lookup_text("   \n\t\nhello", "hello", 2) == 2

# Strict Level 1 Tests
def test_strict1_concatenated_string():
    search_block = "class MyClass:\n    def method():\n        pass"
    search_for = "classMyClass:defmethod():pass"
    assert lookup_text(search_block, search_for, 1) == 0

def test_strict1_partial_match_across_lines():
    assert lookup_text("abc\ndef\nghi", "cdef", 1) == 0

def test_strict1_no_match_due_to_missing_characters():
    assert lookup_text("abcdef", "xyz", 1) == -1

def test_empty_search_block():
    assert lookup_text("", "abc", 1) == -1

def test_search_for_longer_than_block():
    assert lookup_text("a\nb", "a\nb\nc", 4) == -1

def test_multiple_matches_returns_first():
    assert lookup_text("a\nb\na\nb", "a\nb", 4) == 0

def test_match_at_start():
    assert lookup_text("a\nb\nc", "a\nb", 4) == 0

def test_match_at_end():
    assert lookup_text("a\nb\nc", "b\nc", 4) == 1