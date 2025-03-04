from typing import List
import re

def find_shortest_indentation(text: str) -> int:
    """Calculate the minimum indentation in non-empty lines of text.
    
    Analyzes leading whitespace to determine the smallest indentation level
    across all non-empty lines. Empty lines (including whitespace-only) are
    ignored for minimum calculation.
    
    Args:
        text: Input string containing potentially indented lines
        
    Returns:
        Minimum indentation level (number of whitespace characters).
        Returns 0 if no indented lines exist.
    """
    lines = text.splitlines()
    indentations: List[int] = []
    
    for line in lines:
        stripped = line.lstrip()
        if stripped:  # Only consider lines with actual content
            # Calculate indentation by comparing original and stripped lengths
            indent = len(line) - len(stripped)
            indentations.append(indent)
    return min(indentations) if indentations else 0


def unindent(text: str) -> str:
    """Remove uniform indentation from all lines while preserving structure.
    
    The removed indentation amount equals the smallest indentation found
    in the text. Maintains relative indentation levels between lines and
    preserves empty lines without modification.
    
    Args:
        text: Input text block with consistent indentation
        
    Returns:
        Text block with base indentation removed from all lines
    """
    indent_to_remove = find_shortest_indentation(text)
    lines = text.split('\n')
    processed: List[str] = []
    for line in lines:
        # Preserve empty lines and short lines without modification
        if len(line) >= indent_to_remove:
            processed_line = line[indent_to_remove:]
        else:
            processed_line = line
        processed.append(processed_line)
    
    return '\n'.join(processed)


def reindent(original_text: str, new_text: str) -> str:
    """Reapply original code's indentation pattern to new text.
    
    Process:
    1. Find base indentation of original_text
    2. Remove existing indentation from new_text
    3. Apply original's base indentation to unindented new_text
    
    Args:
        original_text: Source text providing indentation pattern
        new_text: Text to reformat using original's indentation
        
    Returns:
        new_text aligned with original_text's base indentation,
        maintaining new_text's internal structure
    """
    base_indent = find_shortest_indentation(original_text)
    unindented = unindent(new_text)

    reindented_lines: List[str] = []
    if "\t" in original_text:
        indent_str = '\t' * base_indent
    else:
        indent_str = ' ' * base_indent
    
    for line in unindented.split('\n'):
        if line.strip():  # Only indent lines with actual content
            reindented_lines.append(f"{indent_str}{line}")
        else:
            # Preserve empty lines and whitespace-only lines
            reindented_lines.append(line)
    return '\n'.join(reindented_lines)

def enumerate_lines(text: str) -> str:
    lines = text.splitlines()
    enumerated_lines = [f"{i} {line}" for i, line in enumerate(lines)]
    return '\n'.join(enumerated_lines)

def remove_codeblock(text: str):
    if "```" not in text:
        return text
    index1 = text.find("```")
    index1n = text.find("\n", index1)
    index2 = text.find("```", index1n + 1)
    return text[index1n:index2].strip()


def unenumerate_lines(text: str) -> tuple[int, list, str]:
    lines = text.splitlines()
    list_lines = []
    list_numbers = []
    num_unenumerated = 0
    # Check for {i} {line} format with singular space
    for line in lines:
        if re.match(r"^\d+\s+", line) is not None:
            list_lines.append(" ".join(line.split(" ")[1:]))
            list_numbers.append(int(line.split(" ")[0]))
            num_unenumerated += 1
        elif is_int(line.strip()):
            list_lines.append("")
            list_numbers.append(int(line))
            num_unenumerated += 1
        else:
            list_lines.append(line)
            list_numbers.append(None)
    return num_unenumerated, list_numbers, "\n".join(list_lines)

def is_int(text: str) -> bool:
    try:
        int(text)
        return True
    except ValueError:
        return False

def equate_code_blocks(text1: str, text2: str):
    text1 = unindent(text1)
    accumul_lines = []
    for line in text1.splitlines():
        line = line.split("#")[0].split("//")[0]
        if len(line.strip()) >= 1:
            accumul_lines.append(line)
    text1 = "\n".join(accumul_lines)

    text2 = unindent(text2)
    accumul_lines = []
    for line in text2.splitlines():
        line = line.split("#")[0].split("//")[0]
        if len(line.strip()) >= 1:
            accumul_lines.append(line)
    text2 = "\n".join(accumul_lines)
    return text1 == text2