import streamlit as st
import json
import os
from agent2.agent.tool_formatter import XMLToolFormatter, JSONToolFormatter, MarkdownToolFormatter, CodeACTToolFormatter
from agent2.agent.agent import Agent
from agent2.utils.agent_utils import save_agent_to_json
from agent2.tools_common.basic_tools.basic_editing import replace_lines, replace_lines_with, replace_block, replace_block_with
from agent2.tools_common.element_tools.element_editing import replace_element, replace_element_with, open_element
from agent2.tools_common.basic_tools.basic_viewing import view_lines, search_files, view_file_raw
from agent2.tools_common.element_tools.element_viewing import view_element, search_elements, semantic_search_elements, view_file
from agent2.agent.tool_settings import ToolSettings
from agent2.agent.tool import Tool


DEFAULT_TEMPLATES = {
    "system_prompt": """You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

Here is the list of folders at the root level that you have access to:
{{top_level_files_list}}

And a summary of file types in the project:
{{filetype_summary}}

To assist you in your tasks, you have the following tools that you are allowed to use; make sure to wrap them within the {{tools_start}} and {{tools_end}} tokens:
{{tools_list}}.

Here are some examples of how to use the tools:
{{tools_examples}}""",

    "init_message": """Below is a github issue that occurs in the files you were given:
{{task}}

Your goal is to find and edit the relevant files to solve the github issue. Before using a tool, explain why you are using the tool (what relevance does it have with the github issue. After using a tool, you will receive some output, reflect on the relevance of the output with the github issue. When you are complete, give a short one paragraph summary of what you've done. You do NOT need to test or run your code. Please do not include line numbers when writing code. You may only use a single tool call per turn. If you cannot find a file, think of an alternative way to fix the issue, do not repeatedly look for a file. Begin by searching for relevant elements within the folders you have access to. Remember to wrap tool calls within {{tools_start}} and {{tools_end}}""",

    "tool_response_wrapper": "{{tool_response}}",
    
    "tool_not_found_error": """Tool '{{tool_name}}' not found. Closest match (if present): {{closest_match}}
Available tools: {{tools_list_name}}""",

    "tool_wrong_arguments_error": """Invalid arguments for '{{tool_name}}'
Wrong arguments: {{wrong_arguments}}
Missing parameters: {{missing_args}}
Unrecognized parameters: {{unrecognized_args}}""",

    "tool_miscellaneous_error": """Miscellaneous error in '{{tool_name}}': 
{{error_message}}"""
}


VARIABLE_HELP = {
    "system_prompt": (
        "Available variables:\n"
        "{{tools_list}} - Formatted tool list\n"
        "{{tools_examples}} - Tool usage examples\n"
        "{{tools_start}}/{{tools_end}} - Tool call delimiters\n"
        "{{filetype_summary}} - File type statistics\n"
        "{{top_level_files_list}} - Top-level directory listing"
    ),
    "init_message": (
        "Available variables:\n"
        "{{task}} - The GitHub issue description\n"
        "All system prompt variables plus:\n"
        "{{elements_saved_text}} - Saved code elements"
    ),
    "response_wrapper": "Variables: {{tool_response}}, {{tool_name}}",
    "not_found_error": "Variables: {{tool_name}}, {{closest_match}}, {{tools_list_name}}",
    "wrong_args_error": "Variables: {{tool_name}}, {{wrong_arguments}}, {{missing_args}}, {{unrecognized_args}}",
    "misc_error": "Variables: {{tool_name}}, {{error_message}}"
}
def agent_builder(available_tools: list):
    st.title("Agent Configuration Builder")
    
    # Path configuration
    agents_path = st.text_input("Agents Directory", "./saved_agents")
    agent_name = st.text_input("Agent Name", "my_agent")
    save_path = os.path.join(agents_path, f"{agent_name}.json")
    
    # Initialize with defaults
    if 'config' not in st.session_state:
        st.session_state.config = {
            'system_prompt': DEFAULT_TEMPLATES['system_prompt'],
            'init_message': DEFAULT_TEMPLATES['init_message'],
            'selected_tools': [],
            'formatter_type': 'XML',
            'tool_formatter': {
                'tool_start': '{{tools_start}}',
                'tool_end': '{{tools_end}}'
            },
            'tool_settings': ToolSettings().__dict__,
            'prompt_templates': {
                'response_wrapper': DEFAULT_TEMPLATES['tool_response_wrapper'],
                'not_found_error': DEFAULT_TEMPLATES['tool_not_found_error'],
                'wrong_args_error': DEFAULT_TEMPLATES['tool_wrong_arguments_error'],
                'misc_error': DEFAULT_TEMPLATES['tool_miscellaneous_error']
            }
        }

    if st.button("Load Agent"):
        if os.path.exists(save_path):
            try:
                with open(save_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                    # Map the formatter type from the saved config
                    if 'tool_formatter' in loaded_config:
                        loaded_config['formatter_type'] = loaded_config['tool_formatter'].get('type', 'XML')
                    
                    # Update session state with loaded config
                    st.session_state.config.update(loaded_config)
                    st.success("Loaded existing configuration!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading agent: {str(e)}")
        else:
            st.warning("No existing agent found.")
    
    # Tool selection
    st.subheader("Tool Selection")
    tool_info = {t.name: t.description for t in available_tools}
    selected_tools = st.multiselect(
        "Available Tools",
        options=list(tool_info.keys()),
        default=st.session_state.config['selected_tools'],
        format_func=lambda x: f"{x} - {tool_info.get(x, 'No description')}"
    )
    
    # Formatter configuration
    st.subheader("Tool Formatter")
    formatter_options = ["JSON", "XML", "Markdown", "CodeAct"]
    current_formatter = st.session_state.config.get('formatter_type', 'XML')
    formatter_type = st.selectbox(
        "Formatter Type",
        options=formatter_options,
        index=formatter_options.index(current_formatter)
    )
    
    # Tool Start and End configuration
    tool_formatter_config = st.session_state.config.get('tool_formatter', {})
    cols = st.columns(2)
    tool_start = cols[0].text_input(
        "Tool Start Token", 
        value=tool_formatter_config.get('tool_start', '{{tools_start}}')
    )
    tool_end = cols[1].text_input(
        "Tool End Token", 
        value=tool_formatter_config.get('tool_end', '{{tools_end}}')
    )
    
    # Tool settings
    st.subheader("Tool Settings")
    settings = st.session_state.config['tool_settings']
    cols = st.columns(2)
    settings['max_search_result_listings'] = cols[0].number_input(
        "Max Search Results", 1, 1000, settings['max_search_result_listings']
    )
    settings['max_search_result_lines'] = cols[1].number_input(
        "Max Search Lines", 1, 1000, settings['max_search_result_lines']
    )
    settings['max_view_lines_start'] = cols[0].number_input(
        "Max View Lines Start", 1, 1000, settings['max_view_lines_start']
    )
    settings['max_view_lines_end'] = cols[1].number_input(
        "Max View Lines End", 1, 1000, settings['max_view_lines_end']
    )
    settings['unindent_inputs'] = cols[0].checkbox(
        "Unindent Inputs", value=settings['unindent_inputs']
    )
    settings['number_lines'] = cols[0].checkbox(
        "Number Lines", value=settings['number_lines']
    )
    settings['reindent_outputs'] = cols[0].checkbox(
        "Reindent Outputs", value=settings['reindent_outputs']
    )
    settings['match_strict_level'] = cols[1].number_input(
        "Match Strict Level", 0, 4, settings['match_strict_level']
    )
    settings['secretly_save'] = cols[0].checkbox(
        "Secretly Save", value=settings['secretly_save']
    )
    settings['embeddings_model_path'] = cols[1].text_input(
        "Embeddings Model Path", value=settings['embeddings_model_path']
    )
    settings['minimum_embeddings_similarity'] = cols[1].number_input(
        "Minimum Embeddings Similarity", 0.0, 1.0, settings['minimum_embeddings_similarity']
    )
    
    # Prompt templates
    st.subheader("Core Prompts")
    system_prompt = st.text_area(
        "System Prompt", 
        value=st.session_state.config['system_prompt'],
        height=300,
        help=VARIABLE_HELP['system_prompt']
    )
    
    init_message = st.text_area(
        "Initial Message", 
        value=st.session_state.config['init_message'],
        height=300,
        help=VARIABLE_HELP['init_message']
    )
    
    # Error templates
    st.subheader("Response Templates")
    response_wrapper = st.text_area(
        "Tool Response Wrapper",
        value=st.session_state.config['prompt_templates']['response_wrapper'],
        help=VARIABLE_HELP['response_wrapper']
    )
    
    st.subheader("Error Templates")
    not_found_error = st.text_area(
        "Tool Not Found Error",
        value=st.session_state.config['prompt_templates']['not_found_error'],
        help=VARIABLE_HELP['not_found_error']
    )
    wrong_args_error = st.text_area(
        "Invalid Arguments Error",
        value=st.session_state.config['prompt_templates']['wrong_args_error'],
        help=VARIABLE_HELP['wrong_args_error']
    )
    misc_error = st.text_area(
        "Miscellaneous Error",
        value=st.session_state.config['prompt_templates']['misc_error'],
        help=VARIABLE_HELP['misc_error']
    )
    
    # Save configuration
    if st.button("Save Agent Configuration"):
        try:
            # Create formatter instance with tool_start and tool_end
            formatter_map = {
                "JSON": JSONToolFormatter(tool_start=tool_start, tool_end=tool_end),
                "XML": XMLToolFormatter(tool_start=tool_start, tool_end=tool_end),
                "Markdown": MarkdownToolFormatter(tool_start=tool_start, tool_end=tool_end),
                "CodeAct": CodeACTToolFormatter(tool_start=tool_start, tool_end=tool_end)
            }
            formatter = formatter_map[formatter_type]
            
            # Create tool settings
            tool_settings = ToolSettings()
            for key, value in settings.items():
                if hasattr(tool_settings, key):
                    setattr(tool_settings, key, value)

            # Create dummy agent for saving
            agent = Agent(
                system_prompt=system_prompt,
                init_message=init_message,
                tools_list=[t for t in available_tools if t.name in selected_tools],
                tool_formatter=formatter,
                tools_settings=tool_settings,
                tool_response_wrapper=response_wrapper,
                tool_not_found_error_wrapper=not_found_error,
                tool_wrong_arguments_error_wrapper=wrong_args_error,
                tool_miscellaneous_error_wrapper=misc_error
            )

            # Save using the utility function
            os.makedirs(agents_path, exist_ok=True)
            save_agent_to_json(agent, save_path)
            st.success(f"Agent saved to {save_path}!")
        except Exception as e:
            st.error(f"Error saving agent: {str(e)}")
            
if __name__ == "__main__":
    tools = [
        Tool(replace_block),
        Tool(replace_block_with),
        Tool(replace_lines),
        Tool(replace_lines_with),
        Tool(replace_element),
        Tool(replace_element_with),
        Tool(view_lines),
        Tool(search_files),
        Tool(view_element),
        Tool(search_elements),
        Tool(semantic_search_elements),
        Tool(view_file),
        Tool(view_file_raw),
        Tool(open_element)
    ]
    agent_builder(tools)