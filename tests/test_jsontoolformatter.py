import pytest
import json
from agent2.agent.tool_formatter import Tool, JSONToolFormatter

@pytest.fixture
def formatter():
    return JSONToolFormatter()

@pytest.fixture
def sample_tool():
    def file_processor(state, settings, path: str, timeout: int = 60, format: str = "enum:json,xml,csv"):
        """Process files in the system
        
        Args:
            path: File path to process
            timeout: Processing timeout in seconds
            format: Output format (json, xml, csv)
            
        Example:
            Process network configuration
            Tool Call:
            {"name": "file_processor", "arguments": {"path": "/etc/config", "timeout": 30}}
        """
        pass
    return Tool(file_processor)

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
        json_str = '{"name": "test", "arguments": {"param1": "value", "param2": 42}}'
        result = formatter.string_to_json(json_str)
        assert result == {
            "name": "test",
            "arguments": {"param1": "value", "param2": 42}
        }

    def test_type_preservation(self, formatter):
        json_str = '''{
            "numbers": [1, 2.5, -3],
            "nested": {"bool": true, "null": null}
        }'''
        result = formatter.string_to_json(json_str)
        assert isinstance(result["numbers"][0], int)
        assert isinstance(result["numbers"][1], float)
        assert result["nested"]["bool"] is True
        assert result["nested"]["null"] is None

    def test_error_handling(self, formatter):
        with pytest.raises(json.JSONDecodeError):
            formatter.string_to_json("{invalid: json}")

        with pytest.raises(ValueError):
            print (formatter.string_to_json('"not an object"'))
            formatter.string_to_json('"not an object"')

class TestJSONToString:
    def test_basic_conversion(self, formatter, sample_json):
        result = formatter.json_to_string(sample_json)
        parsed = json.loads(result)
        assert parsed == sample_json

class TestToolToString:
    def test_schema_structure(self, formatter, sample_tool):
        temp = formatter.tool_to_string(sample_tool)
        temp = temp.split("<tool_call>")[1]
        temp = temp.split("</tool_call>")[0].strip()
        schema = json.loads(temp)
        print(schema)
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "file_processor"
        assert "path" in schema["function"]["parameters"]["required"]
        
        props = schema["function"]["parameters"]["properties"]
        assert props["path"]["type"] == "string"
        assert props["timeout"]["type"] == "integer"
        assert props["format"]["type"] == "string"

    def test_required_vs_optional(self, formatter):
        def test_tool(state, req: str, opt: int = 0):
            """Test tool"""
            pass
        temp = formatter.tool_to_string(Tool(test_tool))
        temp = temp.split("<tool_call>")[1]
        temp = temp.split("</tool_call>")[0].strip()
        schema = json.loads(temp)
        params = schema["function"]["parameters"]
        
        assert "req" in params["required"]
        assert "opt" not in params["required"]
        assert params["properties"]["opt"]["type"] == "integer"

    def test_type_mappings(self, formatter):
        def type_tool(state, 
                    s: str, 
                    i: int, 
                    f: float, 
                    b: bool, 
                    l: list, 
                    d: dict):
            """Type test tool"""
            pass
        temp = formatter.tool_to_string(Tool(type_tool))
        temp = temp.split("<tool_call>")[1]
        temp = temp.split("</tool_call>")[0].strip()
        schema = json.loads(temp)
        props = schema["function"]["parameters"]["properties"]
        
        assert props["s"]["type"] == "string"
        assert props["i"]["type"] == "integer"
        assert props["f"]["type"] == "number"
        assert props["b"]["type"] == "boolean"
        assert props["l"]["type"] == "array"
        assert props["d"]["type"] == "object"

def test_full_roundtrip(formatter, sample_json):
    # JSON -> String -> JSON
    json_str = formatter.json_to_string(sample_json)
    roundtripped = formatter.string_to_json(json_str)
    assert roundtripped == sample_json

def test_tool_validation_roundtrip(formatter, sample_tool):
    # Tool -> Schema -> Validation
    temp = formatter.tool_to_string(sample_tool)
    temp = temp.split("<tool_call>")[1]
    temp = temp.split("</tool_call>")[0].strip()
    schema = json.loads(temp)
    
    valid_call = {
        "name": "file_processor",
        "arguments": {
            "path": "/etc/config",
            "timeout": 30,
            "format": "json"
        }
    }
    
    invalid_call = {
        "name": "file_processor",
        "arguments": {
            "timeout": "hi",  # Wrong type
            "invalid_param": "value"
        }
    }
    
    # Should match the Tool.match() method
    tool = sample_tool
    assert tool.match(valid_call) is None
    assert tool.match(invalid_call) == (
        ["path: File path to process"],
        ["invalid_param"],
        ["timeout: expected int, got str"]
    )
