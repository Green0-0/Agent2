from agent2.file import File
from agent2.llm.chat import Chat
from typing import List
import copy

class AgentState:
    chat = None
    workspace = None
    saved_elements = None
    last_code_block = None

    def __init__(self, chat: Chat, files: List[File] = []):
        self.chat = chat
        self.workspace = files
        self.saved_elements = []
        self.last_code_block = None