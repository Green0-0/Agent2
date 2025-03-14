import streamlit as st
import os
import time
from typing import List
from pathlib import Path
from agent2.agent.agent import Agent
from agent2.file import File
from agent2.utils.utils import get_completion
from agent2.utils.agent_utils import load_agent_from_json
from agent2.utils.utils import load_project_files
from agent2.utils.agent_utils import save_agent_to_json, load_agent_from_json
from agent2.agent.tool_settings import ToolSettings
from agent2.agent.tool import Tool

def load_project_files(root_path="examples/astropy") -> List[File]:
    """Load all files recursively from the specified directory, skipping binary files."""
    root_path = Path(root_path)
    project_files = []
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                relative_path = str(file_path.relative_to(root_path)).replace(os.sep, '/')
                project_files.append(File(relative_path, content))
            except (UnicodeDecodeError, IsADirectoryError):
                continue
    return project_files

def run_agent_interface():
    st.title("GitHub Issue Solver Agent Runner")
    
    # Initialize session state variables if they don't exist
    if 'agent_process' not in st.session_state:
        st.session_state.agent_process = {
            'running': False,
            'step': 0,
            'diffs': [],
            'conversation': []
        }
    
    # Configuration Panel
    with st.expander("⚙️ Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            codebase_path = st.text_input("Codebase Path", "examples/astropy")
            st.session_state.codebase_path = codebase_path
            agent_config_dir = st.text_input("Agent Config Directory", "saved_agents")
            
            agent_files = [f for f in os.listdir(agent_config_dir) if f.endswith(".json")]
            selected_agent = st.selectbox(
                "Select Agent Configuration",
                agent_files,
                format_func=lambda x: x.replace(".json", "")
            )
            
            if st.button("Initialize Agent"):
                try:
                    agent_path = Path(agent_config_dir) / selected_agent
                    st.session_state.agent = load_agent_from_json(
                        str(agent_path)
                    )
                    st.session_state.files = load_project_files(codebase_path)
                    st.success("Agent initialized successfully!")
                except Exception as e:
                    st.error(f"Initialization failed: {str(e)}")
        
        with col2:
            st.subheader("LLM API Settings")
            api_model = st.text_input("Model", "mistral-small-2501")
            api_key = st.text_input("API Key", type="password")
            api_base = st.text_input("API Base URL", "https://api.mistral.ai/v1")
            
            if st.button("Save API Config"):
                st.session_state.api_config = {
                    "model": api_model,
                    "api_key": api_key,
                    "base_url": api_base
                }
                st.success("API configuration saved!")

    # Execution Panel
    if 'api_config' in st.session_state and 'agent' in st.session_state:
        st.divider()
        st.subheader("Issue Processing")
        
        issue = st.text_area("GitHub Issue Description", height=200)
        
        # Start button and turn limit
        col1, col2 = st.columns(2)
        with col1:
            max_turns = st.number_input("Maximum Turns", min_value=1, max_value=50, value=30)
        
        start_button = st.button("Solve Issue", disabled=st.session_state.agent_process['running'] or 'agent' not in st.session_state)
        stop_button = st.button("Stop Agent", disabled=not st.session_state.agent_process['running'])
        
        if start_button and 'agent' in st.session_state:
            # Clear any previous conversation and diffs immediately
            st.session_state.agent_process = {
                'running': True,
                'step': 0,
                'diffs': [],
                'conversation': []
            }
            
            # Create empty containers to immediately clear previous output
            st.empty()  # This will clear previous outputs
            try:
                st.session_state.agent.start(
                    task=issue,
                    files=st.session_state.files
                )
                for file in st.session_state.agent.cached_state.workspace:
                    file.updated_content = file.original_content
                st.rerun()
                # Add initial system message
                st.session_state.agent_process['conversation'].append({
                    "role": "system",
                    "content": f"Agent started with task: {issue[:100]}..." if len(issue) > 100 else f"Agent started with task: {issue}"
                })
                st.rerun()
            except Exception as e:
                st.error(f"Agent start failed: {str(e)}")
                st.session_state.agent_process['running'] = False
        
        if stop_button:
            st.session_state.agent_process['running'] = False
            st.session_state.agent_process['conversation'].append({
                "role": "system",
                "content": "Agent stopped manually by user"
            })
            st.rerun()
        
        # Display real-time conversation
        if st.session_state.agent_process.get('conversation'):
            st.subheader(f"Processing Log (Step {st.session_state.agent_process.get('step', 0)})")
            for msg in st.session_state.agent_process['conversation']:
                with st.chat_message(msg["role"]):
                    if "```" in msg["content"]:
                        st.code(msg["content"].strip("```").strip(), language="json")
                    else:
                        st.write(msg["content"])
        
        # Display real-time diffs
        if st.session_state.agent_process.get('diffs'):
            st.divider()
            st.subheader("Proposed Changes")
            for diff in st.session_state.agent_process['diffs']:
                with st.expander(f"Changes to {diff['path']}"):
                    st.code(diff["diff"], language="diff")
        
        # Process agent step if running
        if st.session_state.agent_process.get('running', False) and 'agent' in st.session_state:
            status_placeholder = st.empty()
            
            with status_placeholder.status("Processing agent step...", expanded=True) as status:
                try:
                    agent = st.session_state.agent
                    current_step = st.session_state.agent_process.get('step', 0)
                    
                    # Check if we've reached the maximum number of turns
                    if current_step >= max_turns:
                        st.session_state.agent_process['running'] = False
                        st.session_state.agent_process['conversation'].append({
                            "role": "system",
                            "content": f"Agent stopped after reaching maximum turns ({max_turns})"
                        })
                        status.update(label="Processing complete (max turns reached)!", state="complete")
                        st.rerun()
                        return
                    
                    # Get current messages
                    oai_messages = agent.cached_state.chat.toOAI()
                    
                    # Get LLM response
                    response = get_completion(
                        oai_messages=oai_messages,
                        model=st.session_state.api_config["model"],
                        api_key=st.session_state.api_config["api_key"],
                        api_url=st.session_state.api_config["base_url"]
                    )
                    
                    if response:
                        result = agent.step(response)
                        
                        # Process response
                        response_trimmed = response.split(agent.tool_formatter.tool_end)[0] if agent.tool_formatter.tool_end in response else response
                        response_parts = response_trimmed.split(agent.tool_formatter.tool_start)
                        
                        # Update conversation
                        new_messages = []
                        if response_parts[0].strip():
                            new_messages.append({
                                "role": "assistant", 
                                "content": response_parts[0].strip()
                            })
                        if len(response_parts) > 1 and response_parts[1].strip():
                            new_messages.append({
                                "role": "assistant",
                                "content": f"```{response_parts[1].strip()}```"
                            })
                        if result and result.tool_response_debug_text:
                            new_messages.append({
                                "role": "system",
                                "content": f"```{result.tool_response_debug_text}```"
                            })
                        
                        st.session_state.agent_process['conversation'].extend(new_messages)
                        st.session_state.agent_process['step'] = current_step + 1
                        
                        # Collect diffs incrementally
                        diffs = []
                        pth = Path(codebase_path)
                        for file in agent.cached_state.workspace:
                            if file.original_content != file.updated_content:
                                file_path = codebase_path / file.path
                                diffs.append({
                                    "path": str(file_path),
                                    "diff": file.diff("astropy"),
                                    "content": file.updated_content
                                })
                        st.session_state.agent_process['diffs'] = diffs
                        
                        # Check completion
                        if result and result.done:
                            st.session_state.agent_process['running'] = False
                            st.session_state.agent_process['conversation'].append({
                                "role": "system",
                                "content": "Agent completed the task successfully"
                            })
                            status.update(label="Processing complete!", state="complete")
                        
                        # Force a rerun to update the UI in real-time
                        status.update(label=f"Step {current_step + 1} complete, continuing...", state="running")
                        time.sleep(0.5)  # Small delay to ensure UI updates
                        st.rerun()
                    
                    else:
                        st.session_state.agent_process['running'] = False
                        st.session_state.agent_process['conversation'].append({
                            "role": "system",
                            "content": "Processing failed - no response from LLM"
                        })
                        status.update(label="Processing failed - no response", state="error")
                        st.rerun()
                
                except Exception as e:
                    st.session_state.agent_process['running'] = False
                    st.session_state.agent_process['conversation'].append({
                        "role": "system",
                        "content": f"Error: {str(e)}"
                    })
                    status.update(label=f"Processing failed: {str(e)}", state="error")
                    st.rerun()

if __name__ == "__main__":
    run_agent_interface()
