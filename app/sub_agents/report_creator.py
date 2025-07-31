from google.adk.agents import Agent

report_creator = Agent(
    name="report_creator",
    model="gemini-2.5-flash",
    instruction="You are a helpful AI assistant designed to provide accurate and useful information."
)