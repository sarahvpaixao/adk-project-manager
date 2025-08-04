# Conteúdo para app/sub_agents/issue_updater.py

from google.adk.agents import Agent

from ..instructions import ISSUE_UPDATER_INSTRUCTIONS
from ..tools import update_jira_issue
from app.config.models import ISSUE_UPDATER_MODEL


issue_updater = Agent(
    name="issue_updater",
    model=ISSUE_UPDATER_MODEL, 
    instruction=ISSUE_UPDATER_INSTRUCTIONS,
    description="Updates existing issues in Jira, such as changing the summary or description.",
    tools=[update_jira_issue]
)