from google.adk.agents import Agent

from ..instructions import TASK_CREATOR_INSTRUCTIONS
from ..tools import get_jira_epics, create_jira_task

from app.config.models import TASK_CREATOR_MODEL


tasks_creator = Agent(
    name="tasks_creator",
    model=TASK_CREATOR_MODEL,
    instruction=TASK_CREATOR_INSTRUCTIONS,
    description="Creates tasks in Jira based on existing epics and provided requirements.",
    output_key="created_tasks",
    tools=[get_jira_epics, create_jira_task]
)
