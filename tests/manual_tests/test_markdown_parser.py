from agent2.formatting.parsers.parse_markdown import parse_markdown_elements
from agent2.element import Element

# COMPLETELY BROKEN

def debug_parse_and_print(markdown: str):
    print("=== TESTING PARSER ON THIS MARKDOWN ===")
    # Line the markdown, starting with zero
    
    for i, line in enumerate(markdown.split("\n")):
        print(f"{i} | {line}")
    print("\n=== PARSER OUTPUT ===")
    
    elements = parse_markdown_elements(markdown)
    
    def print_element(element: Element, indent=0):
        prefix = "  " * indent
        print(f"{prefix}Identifier: {element.identifier}")
        print(f"{prefix}Start line: {element.line_start}")
        print(f"{prefix}Docstring: {element.description + '...' if element.description else ''}")
        
        # Determine content length to show a meaningful preview
        content_lines = element.content.split('\n')
        if len(content_lines) > 3:
            preview = '\n'.join(content_lines[:3]) + "..."
        else:
            preview = element.content
            
        print(f"{prefix}Content preview: {preview}")
        print(f"{prefix}Contains {len(element.elements)} sub-elements")
        
        for child in element.elements:
            print()
            print_element(child, indent + 1)
    
    for idx, elem in enumerate(elements):
        print(f"Top-level element #{idx + 1}:")
        print_element(elem)
        print("\n" + "-" * 80 + "\n")

# Test case 1: Basic markdown with heading hierarchy
test_markdown_1 = '''# Main Heading

Some paragraph text here.

## Section 1

This is a section with some content.

### Subsection 1.1

- List item 1
- List item 2
  - Nested list item
- List item 3

## Section 2

```
def hello_world():
    print("Hello, World!")
```

### Subsection 2.1

Here is a table:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |

#### Deep nested heading

Text in deep nested section.
'''

debug_parse_and_print(test_markdown_1)

# Test case 2: Edge cases and complex formatting
test_markdown_2 = '''# Document with Edge Cases

## Code blocks with different languages

```
class Example:
    def method(self):
        pass
```

```
function example() {
  return true;
}
```

```
Plain code block without language
```

## Blockquotes and nested elements

> This is a blockquote
> With multiple lines
> 
> > And a nested blockquote
> > With its own contents

## Setext headings
This is an H1
=============

This is an H2
-------------

## Mixed content

* List with a code block:
  ```
  {"key": "value"}
  ```

* List with a table:
  | Name | Value |
  |------|-------|
  | Key  | Val   |
'''

debug_parse_and_print(test_markdown_2)