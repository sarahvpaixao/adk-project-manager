from google.adk.agents import Agent
from ..instructions import TASK_CREATOR_INSTRUCTIONS
from ..tools import get_jira_epics, create_jira_task

tasks_creator = Agent(
    name="tasks_creator",
    model="gemini-2.5-flash",
    instruction=TASK_CREATOR_INSTRUCTIONS,
    description="Creates tasks in Jira based on existing epics and provided requirements.",
    output_key="created_tasks",
    tools=[get_jira_epics, create_jira_task]
)
