import pytest
import json
from agent2.agent.tool import Tool
from agent2.agent.agent_state import AgentState
from typing import Dict, List


class TestTool:
    def test_basic_initialization(self):
        """Test basic tool initialization with a simple function."""
        def simple_tool(state: AgentState, query: str):
            """Search for information.
            
            Args:
                state: The agent state
                query: The search query
            """
            pass
        
        tool = Tool(simple_tool)
        
        assert tool.name == "simple_tool"
        assert tool.description == "Search for information."
        assert len(tool.required_args) == 1
        assert tool.required_args[0][0] == "query"
        assert "The search query" in tool.required_args[0][1]
        assert tool.required_args[0][2] == "str"
        assert len(tool.optional_args) == 0
        assert not hasattr(tool, "example_task") or tool.example_task is None
        assert not hasattr(tool, "example_tool_call") or tool.example_tool_call is None

    def test_optional_arguments(self):
        """Test tool with optional arguments."""
        def complex_tool(state: AgentState, query: str, limit: int = 5, filter: bool = False):
            """Perform complex search with filters.
            
            Args:
                state: The agent state
                query: The search query
                limit: Maximum number of results
                filter: Whether to apply filtering
            """
            pass
        
        tool = Tool(complex_tool)
        
        assert tool.name == "complex_tool"
        assert tool.description == "Perform complex search with filters."
        
        # Required args
        assert len(tool.required_args) == 1
        assert tool.required_args[0][0] == "query"
        assert "The search query" in tool.required_args[0][1]
        assert tool.required_args[0][2] == "str"
        
        # Optional args
        assert len(tool.optional_args) == 2
        
        # Check limit parameter
        limit_arg = next((arg for arg in tool.optional_args if arg[0] == "limit"), None)
        assert limit_arg is not None
        assert "Maximum number of results" in limit_arg[1]
        assert limit_arg[2] == "int"
        
        # Check filter parameter
        filter_arg = next((arg for arg in tool.optional_args if arg[0] == "filter"), None)
        assert filter_arg is not None
        assert "Whether to apply filtering" in filter_arg[1]
        assert filter_arg[2] == "bool"

    def test_example_usage(self):
        """Test tool with example usage."""
        def example_tool(state: AgentState, filename: str):
            """Read a file's contents.
            
            Args:
                state: The agent state
                filename: Name of the file to read
                
            Example:
            I need to read the contents of config.json
            
            Tool Call:
            {
                "name": "example_tool",
                "arguments": {
                    "filename": "config.json"
                }
            }
            """
            pass
        
        tool = Tool(example_tool)
        
        assert tool.name == "example_tool"
        assert tool.description == "Read a file's contents."
        assert len(tool.required_args) == 1
        assert tool.required_args[0][0] == "filename"
        assert "Name of the file to read" in tool.required_args[0][1]
        assert tool.required_args[0][2] == "str"
        assert len(tool.optional_args) == 0
        
        # Check example content
        assert hasattr(tool, "example_task")
        assert tool.example_task == "I need to read the contents of config.json"
        assert hasattr(tool, "example_tool_call")
        assert tool.example_tool_call["name"] == "example_tool"
        assert tool.example_tool_call["arguments"]["filename"] == "config.json"

    def test_tool_function_calling(self):
        """Test calling the tool function."""
        def add_numbers(state: AgentState, a: int, b: int):
            """Add two numbers together.
            
            Args:
                state: The agent state
                a: First number
                b: Second number
            """
            return a + b
        
        tool = Tool(add_numbers)
        
        assert tool.name == "add_numbers"
        assert tool.description == "Add two numbers together."
        assert len(tool.required_args) == 2
        
        # Test actual function call
        mock_state = AgentState(None)
        result = tool(mock_state, 5, 3)
        assert result == 8
        
        # Alternative call method
        result = tool.func(mock_state, 5, 3)
        assert result == 8

    def test_invalid_json_example(self):
        """Test with invalid example JSON."""
        def invalid_example_tool(state: AgentState):
            """A tool with invalid JSON example.
            
            Args:
                state: The agent state
                
            Example:
            Testing invalid JSON
            
            Tool Call:
            {
                "name": "invalid_example
                "arguments": {
                }
            }
            """
            pass
        
        with pytest.raises(ValueError, match="Invalid JSON in example tool call"):
            Tool(invalid_example_tool)

    def test_complex_parameter_types(self):
        """Test with complex parameter types."""
        def complex_types_tool(state: AgentState, data: Dict[str, List[int]]):
            """Process structured data.
            
            Args:
                state: The agent state
                data: Dictionary mapping strings to lists of integers
            """
            pass
        
        tool = Tool(complex_types_tool)
        
        assert tool.name == "complex_types_tool"
        assert tool.description == "Process structured data."
        assert len(tool.required_args) == 1
        assert tool.required_args[0][0] == "data"
        assert "Dictionary mapping strings to lists of integers" in tool.required_args[0][1]
        # Note: Complex types might be simplified to their base type
        assert tool.required_args[0][2] in ["dict", "Dict"]

    def test_multiple_arguments(self):
        """Test with multiple required and optional arguments."""
        def advanced_tool(state: AgentState, query: str, dataset: str, limit: int = 10, 
                         sort: bool = True, format: str = "json"):
            """Advanced data query tool.
            
            Args:
                state: The agent state
                query: The search query string
                dataset: The dataset name to search in
                limit: Maximum number of results to return
                sort: Whether to sort results
                format: Output format (json, csv, xml)
            """
            pass
        
        tool = Tool(advanced_tool)
        
        assert tool.name == "advanced_tool"
        assert tool.description == "Advanced data query tool."
        
        # Required args
        assert len(tool.required_args) == 2
        
        query_arg = next((arg for arg in tool.required_args if arg[0] == "query"), None)
        assert query_arg is not None
        assert "The search query string" in query_arg[1]
        
        dataset_arg = next((arg for arg in tool.required_args if arg[0] == "dataset"), None)
        assert dataset_arg is not None
        assert "The dataset name to search in" in dataset_arg[1]
        
        # Optional args
        assert len(tool.optional_args) == 3
        
        limit_arg = next((arg for arg in tool.optional_args if arg[0] == "limit"), None)
        assert limit_arg is not None
        assert "Maximum number of results to return" in limit_arg[1]
        
        sort_arg = next((arg for arg in tool.optional_args if arg[0] == "sort"), None)
        assert sort_arg is not None
        assert "Whether to sort results" in sort_arg[1]
        
        format_arg = next((arg for arg in tool.optional_args if arg[0] == "format"), None)
        assert format_arg is not None
        assert "Output format" in format_arg[1]