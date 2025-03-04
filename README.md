Agents2 is a library for building and using agents! 

![streamlitui1](https://github.com/user-attachments/assets/3bffb14f-6e2a-441a-b266-d5728e1020c5)
![streamlitui2](https://github.com/user-attachments/assets/370bf5eb-1b5b-4b53-baf9-7d241f8ef6b4)
![streamlitui3](https://github.com/user-attachments/assets/5b16353a-bb1f-464a-992c-1072d8ece226)
![streamlitui4](https://github.com/user-attachments/assets/80efc765-eb45-4d5e-9fac-7fcecc07e586)
![streamlitui5](https://github.com/user-attachments/assets/86fb0007-bcb2-4c6b-a1c7-b783edacab6a)
![streamlitui6](https://github.com/user-attachments/assets/fc98d005-54c9-4ab7-8023-0735897e9cb2)


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
