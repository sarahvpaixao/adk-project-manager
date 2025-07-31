from google.adk.agents import Agent

epics_creator = Agent(
    name="epics_creator",
    model="gemini-2.5-flash",
    instruction="You are a helpful AI assistant designed to provide accurate and useful information."
)