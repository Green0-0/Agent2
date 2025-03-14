class Chat:
    system_prompt: str # system prompt
    messages: list[str] # list of messages in this chat
    max_retrieves: int # Number of messages to retrieve on toOAI

    def __init__(self, message : str = "", system_prompt = "", max_retrieves : int = 60):
        """
        Create a new chat with an optional starting message and an optional system prompt.

        Args:
            message (str): optional starting message for the chat
            system_prompt (str): optional system prompt for the chat
            max_retrieves (int): optional maximum number of messages to retrieve
        """
        # Standard constructor behavior
        if message == "":
            self.messages = []
        else:
            self.messages = [message]
        self.system_prompt = system_prompt
        self.max_retrieves = max_retrieves
    
    def append(self, message : str):
        """Append message to the end of the message list, making it the new final message."""
        self.messages.append(message)
    
    def appendContinue(self, message : str):
        """Append message to the end of the final message in the message list."""
        self.messages[-1] += message
        
    def toOAI(self):
        """
        Convert the message list to an OpenAI API compatible list of messages.

        Returns:
            list[dict]: List of messages formatted for OpenAI API.
        """
        oai_messages = []
        if self.system_prompt != "":
            oai_messages.append({"role": "system", "content": self.system_prompt})
        for i, msg in enumerate(self.messages):
            role = "user" if i % 2 == 0 else "assistant"
            oai_messages.append({"role": role, "content": msg})
        while len(oai_messages) > self.max_retrieves:
            oai_messages.pop(0)
            oai_messages.pop(0)
        return oai_messages
    
    def decay():
        pass
    
    def __str__(self):
        """
        Overload the __str__ method to convert the Chat object to a string representation.

        Returns:
            str: String representation of the Chat object.
        """
        messages = ["System Prompt: " + self.system_prompt]
        for i, message in enumerate(self.messages):
            role = "User" if i % 2 == 0 else "Assistant"
            messages.append(f"{role}: {message}")
        return "\n\n".join(messages)