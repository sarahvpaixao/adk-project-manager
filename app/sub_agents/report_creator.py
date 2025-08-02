from google.adk.agents import Agent

from ..instructions import REPORT_CREATOR_INSTRUCTIONS
from ..tools import get_jira_project_status, get_jira_epics

from app.config.models import REPORT_CREATOR_MODEL


report_creator = Agent(
    name="report_creator",
    model=REPORT_CREATOR_MODEL,
    instruction=REPORT_CREATOR_INSTRUCTIONS,
    description="Generates comprehensive analytics reports about Jira project status, epics, and tasks for project management insights.",
    output_key="project_report",
    tools=[get_jira_project_status, get_jira_epics]
)
