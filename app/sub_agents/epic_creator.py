from google.adk.agents import Agent

from ..tools.integrations.jira import create_jira_epic
from app.instructions import EPIC_CREATOR_INSTRUCTIONS


epic_creator = Agent(
    name="epic_creator",
    model="gemini-2.5-flash",
    instruction=EPIC_CREATOR_INSTRUCTIONS,
    tools=[
        create_jira_epic
        ]
)
