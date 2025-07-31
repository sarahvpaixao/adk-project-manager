from google.adk.agents import Agent

user_stories_creator = Agent(
    name="user_stories_creator",
    model="gemini-2.5-flash",
    instruction="You are a helpful AI assistant designed to provide accurate and useful information."
)
