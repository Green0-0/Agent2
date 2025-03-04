Agents2 is a library for building and using agents! 

We have:
- Support for agents that run code (using the python sandbox from smolagents), agents that run tools in markdown, xml, or plain json
- Full code parsing with tree-sitter-languages (note that currently only python is supported, but more languages will be added later)
- Code reformatting, so that LLM outputs don't have the wrong spaces/tabs
- A UI to build agents (ui/agent_builder.py) and a UI to test agents (ui/agent_runner.py)

WIP:
- Fast embeddings models (no recomputing docs for entire files, just the parts that were edited)
- OpenAI tool calling format (this is a maybe, depending on whether or not its effective)
- Context decay (replace past tool calls with a summarized version to slash down on context use)
- A better UI
- create_file, write_file
- Two step editing (gurantees proper edits, and can summarize changes): open_and_write, view_and_replace_element

# Updates:
3/2/25 - v0.01 Finally done... 