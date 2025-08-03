import os
from google.adk.agents import Agent

from app.instructions import ROOT_INSTRUCTIONS
from .sub_agents.epic_creator import epic_creator
from .sub_agents.tasks_creator import tasks_creator
from .sub_agents.report_creator import report_creator

_, project_id = google.auth.default()
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=ROOT_INSTRUCTIONS,
    sub_agents=[
        epic_creator,
        tasks_creator,
        report_creator
    ],
    description="Root agent for project management tasks, coordinating sub-agents to create epics, tasks, and reports in Jira."
)
