search_block = """def tool_to_string(self, tool: Tool) -> str:
    tool_doc = tool.func.__doc__
    if "Example:" in tool_doc:
        tool_doc = tool_doc.split("Example:")[0].strip()
    tool_signature = str(inspect.signature(tool.func))
    index1 = tool_signature.find("settings")
    index2 = tool_signature.find(",", index1)
    tool_signature = "def " + tool.name + "(" + tool_signature[index2 + 1:].strip()
    return f"{self.tool_start}\n```python\n" + tool_signature + "\n\"\"\"\n" + tool_doc + "\n\"\"\"\n```\n" + self.tool_end"""

search_for = """def tool_to_string(self, tool: Tool) -> str:
    \"\"\"
    Convert a Tool to a CodeACT string representation.

    This method converts a Tool object into a CodeACT string that includes the tool's
    name, description, and function signature.

    Args:
        tool (Tool): The Tool object to be converted to a CodeACT string.

    Returns:
        str: A CodeACT string representing the Tool object.
    \"\"\"
    tool_doc = tool.func.__doc__
    if "Example:" in tool_doc:
        tool_doc = tool_doc.split("Example:")[0].strip()
    tool_signature = str(inspect.signature(tool.func))
    index1 = tool_signature.find("settings")
    index2 = tool_signature.find(",", index1)
    tool_signature = "def " + tool.name + "(" + tool_signature[index2 + 1:].strip()
    return f"{self.tool_start}\n```python\n" + tool_signature + "\n\"\"\"\n" + tool_doc + "\n\"\"\"\n```\n" + self.tool_end"""
from agent2.formatting.lookup import lookup_text

print(lookup_text(search_block, search_for, strict_level=1))