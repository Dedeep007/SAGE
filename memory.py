from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import threading
import time

class TwoTierMemory:
    def __init__(self, groq_api_key: str):
        self.short_term = ConversationBufferWindowMemory(k=5, memory_key="chat_history", return_messages=True)
        self.system_context = "This is the initial system context. You are an AI agent that controls the screen.\n"
        self.groq_api_key = groq_api_key
        self.isRunning = True

        # start background thread
        self.summary_thread = threading.Thread(target=self._background_summarize, daemon=True)
        self.summary_thread.start()

    def add_interaction(self, user_msg: str, ai_msg: str):
        self.short_term.save_context({"input": user_msg}, {"output": ai_msg})

    def get_context(self) -> str:
        messages = self.short_term.load_memory_variables({})
        recent_history = messages.get("chat_history", [])
        return f"{self.system_context}\n\nRecent History:\n{recent_history}"

    def stop(self):
        self.isRunning = False

    def _background_summarize(self):
        # We summarize every N seconds if new interactions happen (simplified here for demo)
        while self.isRunning:
            time.sleep(60) # Summarize every minute
            messages = self.short_term.chat_memory.messages
            if len(messages) >= 8:
                try:
                    llm = ChatGroq(temperature=0, api_key=self.groq_api_key, model_name="llama-3.3-70b-versatile")
                    prompt = f"Summarize these interactions into a concise factual summary. Keep the most important details.\n\n{messages}"
                    response = llm.invoke(prompt)
                    
                    self.system_context += f"\nSummary of past events: {response.content}"
                    # Clear out part of the memory, or just keep window moving
                    # ConversationBufferWindowMemory handles removing old messages automatically, so we don't strictly need to clear.
                except Exception as e:
                    print(f"Summarizer error: {e}")
