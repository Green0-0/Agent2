import pytest
from agent2.agent.tool_formatter import Tool, MarkdownToolFormatter

@pytest.fixture
def formatter():
    return MarkdownToolFormatter()

@pytest.fixture
def sample_tool():
    def file_processor(state, settings, path: str, timeout: int = 60):
        """Process files in the system
        
        Args:
            path: File path to process
            timeout: Processing timeout in seconds
        """
        pass
    tool = Tool(file_processor)
    return tool

@pytest.fixture
def sample_json():
    return {
        "name": "network_config",
        "arguments": {
            "interface": "eth0",
            "mtu": 1500,
            "enabled": True
        }
    }

class TestStringToJSON:
    def test_valid_conversion(self, formatter):
        md = (
            "## Name: test\n"
            "### arg1: value\n"
            "### arg2: 42\n"
        )
        result = formatter.string_to_json(md)
        assert result == {
            "name": "test",
            "arguments": {"arg1": "value", "arg2": 42}
        }

    def test_type_conversion(self, formatter):
        md = (
            "## Name: types\n"
            "### int: 42\n"
            "### float: 3.14\n"
            "### bool: true\n"
        )
        result = formatter.string_to_json(md)
        assert result["arguments"]["int"] == 42
        assert result["arguments"]["float"] == 3.14
        assert result["arguments"]["bool"] is True

    def test_multiline_values(self, formatter):
        md = (
            "## Name: multiline\n"
            "### content: Line 1\n"
            "Line 2\n"
            "    Indented line\n"
        )
        result = formatter.string_to_json(md)
        assert result["arguments"]["content"] == "Line 1\nLine 2\n    Indented line"

    def test_error_handling(self, formatter):
        # Invalid first line
        with pytest.raises(KeyError):
            formatter.string_to_json("## Invalid: test")

        # Duplicate parameters
        md = (
            "## Name: test\n"
            "### param: value\n"
            "### param: another\n"
        )
        with pytest.raises(ValueError):
            formatter.string_to_json(md)

class TestJSONToString:
    def test_valid_conversion(self, formatter, sample_json):
        result = formatter.json_to_string(sample_json)
        expected = (
            "## Name: network_config\n"
            "### interface: eth0\n"
            "### mtu: 1500\n"
            "### enabled: True\n"
        )
        assert result.strip() == expected.strip()

    def test_multiline_values(self, formatter):
        json_data = {
            "name": "multiline",
            "arguments": {"content": "Line 1\nLine 2\n    Indented"}
        }
        result = formatter.json_to_string(json_data)
        assert "### content: Line 1\nLine 2\n    Indented" in result

    def test_empty_arguments(self, formatter):
        json_data = {"name": "empty", "arguments": {}}
        result = formatter.json_to_string(json_data)
        expected = "## Name: empty"
        assert result.strip() == expected.strip()

class TestToolToString:
    def test_basic_conversion(self, formatter, sample_tool):
        result = formatter.tool_to_string(sample_tool)
        expected = (
            "# Tool Use\n"
            "## Name: file_processor\n"
            "### Description: Process files in the system\n"
            "### path (str, required): File path to process\n"
            "### timeout (int, optional): Processing timeout in seconds\n"
            "# Tool End"
        )
        assert result == expected

    def test_no_optional_args(self, formatter):
        def simple_tool(state, settings, input: str):
            """Basic tool
            
            Args:
                input: Input data
            """
            pass
        tool = Tool(simple_tool)
        
        result = formatter.tool_to_string(tool)
        assert "### input (str, required): Input data" in result
        assert "optional" not in result

    def test_missing_descriptions(self, formatter):
        def minimal(state, settings, param1: int, param2: bool = False):
            pass
        tool = Tool(minimal)
        
        result = formatter.tool_to_string(tool)
        assert "### param1 (int, required): " in result
        assert "### param2 (bool, optional): " in result

def test_full_roundtrip(formatter, sample_json):
    # JSON -> Markdown -> JSON
    md = formatter.json_to_string(sample_json)
    roundtripped = formatter.string_to_json(md)
    assert roundtripped == sample_json