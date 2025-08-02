from google.adk.agents import Agent

from app.instructions import EPIC_CREATOR_INSTRUCTIONS
from ..tools.integrations.jira import create_jira_epic

from app.config.models import EPIC_CREATOR_MODEL


epic_creator = Agent(
    name="epic_creator",
    model=EPIC_CREATOR_MODEL,
    instruction=EPIC_CREATOR_INSTRUCTIONS,
    tools=[
        create_jira_epic
        ]
)
