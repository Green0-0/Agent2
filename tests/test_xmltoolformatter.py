import pytest
from agent2.agent.tool_formatter import Tool, XMLToolFormatter

@pytest.fixture
def formatter():
    return XMLToolFormatter()

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
        xml = "<name>test</name>\n<arg1>value</arg1>\n<arg2>42</arg2>"
        result = formatter.string_to_json(xml)
        assert result == {
            "name": "test",
            "arguments": {"arg1": "value", "arg2": 42}
        }

    def test_type_conversion(self, formatter):
        xml = "<name>types</name>\n<int>42</int>\n<float>3.14</float>\n<bool>true</bool>"
        result = formatter.string_to_json(xml)
        assert result["arguments"]["int"] == 42
        assert result["arguments"]["float"] == 3.14
        assert result["arguments"]["bool"] is True

    def test_xml_escaping(self, formatter):
        xml = "<name>escape</name>\n<text>1 &lt; 2 &amp; 3 &gt; 4</text>"
        result = formatter.string_to_json(xml)
        assert result["arguments"]["text"] == "1 < 2 & 3 > 4"

    def test_error_handling(self, formatter):
        with pytest.raises(ValueError) as e:
            formatter.string_to_json("<name>test</name>\n<arg>no closing tag")
        assert "no closing tag" in str(e.value)

        with pytest.raises(ValueError):
            formatter.string_to_json("invalid first line\n<arg>value</arg>")

        with pytest.raises(ValueError):
            formatter.string_to_json("<name>test</name>\n<arg>value</different>")

class TestJSONToString:
    def test_valid_conversion(self, formatter, sample_json):
        result = formatter.json_to_string(sample_json)
        expected = (
            "<name>network_config</name>\n"
            "<interface>eth0</interface>\n"
            "<mtu>1500</mtu>\n"
            "<enabled>True</enabled>"
        )
        assert result == expected

    def test_xml_escaping(self, formatter):
        json_data = {
            "name": "escape_test",
            "arguments": {"text": "AT&T & <Google>"}
        }
        result = formatter.json_to_string(json_data)
        assert "AT&amp;T &amp; &lt;Google&gt;" in result

    def test_empty_arguments(self, formatter):
        json_data = {"name": "empty", "arguments": {}}
        result = formatter.json_to_string(json_data)
        assert result == "<name>empty</name>"

class TestToolToString:
    def test_basic_conversion(self, formatter, sample_tool):
        result = formatter.tool_to_string(sample_tool)
        expected = (
            "<tool_call>\n"
            "<name>file_processor</name>\n"
            "<description>Process files in the system</description>\n"
            "<path>Required (str): File path to process</path>\n"
            "<timeout>Optional (int): Processing timeout in seconds</timeout>\n"
            "</tool_call>"
        )
        assert result == expected

    def test_no_optional_args(self, formatter):
        def simple_tool(state, input: str):
            """Basic tool
            
            Args:
                input: Input data
            """
            pass
        tool = Tool(simple_tool)
        
        result = formatter.tool_to_string(tool)
        assert "<input>Required (str): Input data</input>" in result
        assert "Optional" not in result

    def test_missing_descriptions(self, formatter):
        def minimal(param1: int, param2: bool = False):
            pass
        tool = Tool(minimal)
        
        result = formatter.tool_to_string(tool)
        assert "<param1>Required: (int)</param1>" in result
        assert "<param2>Optional: (bool)</param2>" in result

def test_full_roundtrip(formatter, sample_json):
    # JSON -> XML -> JSON
    xml = formatter.json_to_string(sample_json)
    roundtripped = formatter.string_to_json(xml)
    assert roundtripped == sample_json
