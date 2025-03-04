import re
import bisect
from typing import List
from agent2.formatting.autoformatter import unindent

def lookup_text(search_block: str, search_for: str, strict_level: int = 3, case_sensitive = False) -> int:
    """Find the starting line number of a search pattern in a text block.
    
    The matching behavior varies by strictness level, with different handling of
    whitespace, indentation, and line breaks. Line numbers are 0-indexed.

    With strict_level 4, match blocks exactly but ignore empty lines.
    With strict_level 3, match unindented versions and ignore empty lines.
    With strict_level 2, match stripped lines and ignore empty lines.
    With strict_level 1, match whitespace-free versions of both texts.
    
    Args:
        search_block: The multi-line text to search within
        search_for: The multi-line pattern to search for
        strict_level: Matching strictness from 1 (lenient) to 4 (strictest)
        case_sensitive: True to perform case-sensitive matching
        
    Returns:
        int: Line number where match starts, or -1 if no match found
        
    Raises:
        ValueError: For invalid strict_level values
    """
    
    def find_subsequence(block_lines: list, for_lines: list) -> int:
        """Find first occurrence of for_lines sequence in block_lines.
        
        Helper for strict levels 2-4. Performs exact sequence matching.
        
        Args:
            block_lines: List of processed lines from search_block
            for_lines: List of processed lines from search_for
            
        Returns:
            int: Starting index in block_lines, or -1 if not found
        """
        len_for = len(for_lines)
        len_block = len(block_lines)
        if len_for == 0:
            return -1
        # Slide window through block lines to find pattern
        for i in range(len_block - len_for + 1):
            if block_lines[i:i+len_for] == for_lines:
                return i
        return -1

    def preprocess_block_lines(block: str, strict_level: int, is_search_block: bool = True) -> list:
        """Process text lines according to strictness level rules.
        
        Handles strict levels 2-4. For search_block, preserves original line numbers.
        
        Args:
            block: Input text to process
            strict_level: Current matching strictness level
            is_search_block: True if processing search_block, False for search_for
            
        Returns:
            list: Processed lines with original line numbers (if search_block)
        """
        lines = block.split('\n')
        processed_lines = []

        if strict_level == 4:
            # Level 4: Exact match but ignore empty lines
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if stripped_line:
                    # Preserve original lines with empty lines removed
                    if is_search_block:
                        processed_lines.append((i, line))  # (original line number, original content)
                    else:
                        processed_lines.append(line)

        elif strict_level == 3:
            # Level 3: Match unindented versions, ignore empty lines
            unindented_block = unindent(block)
            unindented_lines = unindented_block.split('\n')
            for original_line_number, line in enumerate(unindented_lines):
                stripped_line = line.strip()
                if stripped_line:
                    # Map back to original line numbers through unindent
                    if is_search_block:
                        processed_lines.append((original_line_number, line))
                    else:
                        processed_lines.append(line)

        elif strict_level == 2:
            # Level 2: Match stripped lines, ignore empty lines
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if stripped_line:
                    processed_line = stripped_line
                    if is_search_block:
                        processed_lines.append((i, processed_line))
                    else:
                        processed_lines.append(processed_line)
        
        return processed_lines

    def preprocess_block_strict1(block: str, is_search_block: bool = True) -> tuple:
        """Process text for strict level 1 by removing all whitespace.
        
        Creates concatenated string and tracks character offsets per line.
        
        Args:
            block: Input text to process
            is_search_block: True if processing search_block
            
        Returns:
            tuple: (concatenated string, cumulative lengths list) if search_block
                   concatenated string otherwise
        """
        lines = block.split('\n')
        processed_lines = []
        cumulative_lengths = [0]  # Track character count per line for offset mapping
        current_length = 0

        for line in lines:
            # Remove all whitespace from line
            processed_line = re.sub(r'\s+', '', line)
            processed_lines.append(processed_line)
            current_length += len(processed_line)
            cumulative_lengths.append(current_length)

        concatenated = ''.join(processed_lines)

        if is_search_block:
            return concatenated, cumulative_lengths
        else:
            return concatenated

    # Validate strict_level before processing
    if strict_level not in [1, 2, 3, 4]:
        raise ValueError("strict_level must be 1, 2, 3, or 4")
    
    if not case_sensitive:
        search_block = search_block.lower()
        search_for = search_for.lower()

    # Handle strict level 1 separately due to different processing
    if strict_level == 1:
        # Process both texts into whitespace-free concatenations
        block_concatenated, cumulative_lengths = preprocess_block_strict1(search_block)
        for_concatenated = preprocess_block_strict1(search_for, is_search_block=False)
        
        # Find substring position in concatenated strings
        start_index = block_concatenated.find(for_concatenated)
        if start_index == -1:
            return -1
            
        # Map character index back to original line number
        line_index = bisect.bisect_right(cumulative_lengths, start_index) - 1
        return line_index

    else:
        # Process both texts according to strictness rules
        processed_block = preprocess_block_lines(search_block, strict_level)
        processed_for = preprocess_block_lines(search_for, strict_level, is_search_block=False)
        
        # Extract processed lines for matching
        block_lines = [line for (_, line) in processed_block]
        for_lines = processed_for
        
        # Find matching subsequence
        start_index = find_subsequence(block_lines, for_lines)
        if start_index == -1:
            return -1
            
        # Return original line number from search_block processing
        original_line_number = processed_block[start_index][0]
        return original_line_number