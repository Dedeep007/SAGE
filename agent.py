from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_groq import ChatGroq
from tools import TOOLS
from memory import TwoTierMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class DesktopAgent:
    def __init__(self, api_key: str):
        # Using specific model supported for native Groq prompt-caching
        self.llm = ChatGroq(temperature=0, api_key=api_key, model_name="openai/gpt-oss-120b")
        self.tools = TOOLS
        self.memory = TwoTierMemory(api_key)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are SAGE, an advanced Autonomous Desktop AI assistant. You control a computer using tools.
Your goal is to help the user by reading the screen, clicking on elements, and opening applications when requested.

### Previous Context & Memory
{context}

### Instructions & Rules
1. ALWAYS use the provided tools natively. Don't reply with code, just use the tools!
2. CONTINUOUS VISUAL GROUNDING: Your physical actions (clicking, typing) run instantly. However, the screen layout changes completely after every action. The tools will automatically return a visual summary of the screen after they execute. You MUST read these observations carefully to check if a random popup, error, or blocker appeared!
3. Use the MACRO TOOLS! If the user asks you to click something, use `find_and_click_tool("element description")`. If the user asks you to type into a web page, use `find_click_and_type_tool("element description, text to type")`!
4. BE SPATIALLY SPECIFIC: When giving instructions to Macro Tools, provide precise physical locations to prevent false-positives (e.g., use 'Chrome URL address bar at the very top' instead of just 'search bar', otherwise the vision model might click a youtube search bar by mistake).
5. ADAPT TO UNEXPECTED STATES: If an app opens into a previously cached or cluttered state (like a previously left-open website tab) rather than a clean slate, adapt logically! Use native hotkeys (like `ctrl+t` to force a clean tab) to reset the environment rather than blindly trying to force actions into the wrong context.
6. If you observe an ambiguous menu blocker natively, immediately stop tooling and ask the Human which profile/option to select!
7. To find a file or open a local app quickly: press the Windows key using `press_key_tool` ("win"), use `type_text_immediately_tool` to type the search query or app name, and then use `press_key_tool` ("enter") to open it.

If you desire to respond to the user, just output natural text. Stop using tools when your goal is complete!"""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def run(self, command: str, callbacks=None) -> str:
        ctx = self.memory.get_context()
        try:
            response = self.agent_executor.invoke({"input": command, "context": ctx}, config={"callbacks": callbacks} if callbacks else None)
            output = response.get("output", "Done.")
            self.memory.add_interaction(command, output)
            return output
        except Exception as e:
            return f"Agent encountering error: {e}"

    def stop(self):
        self.memory.stop()
