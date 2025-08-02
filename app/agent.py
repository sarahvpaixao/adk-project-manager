# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from google.adk.agents import Agent
from .sub_agents.user_stories_creator import user_stories_creator
from .sub_agents.epics_creator import epics_creator
from .sub_agents.report_creator import report_creator

# Set default environment variables for Google Cloud project and location
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "polar-scarab-467503-f9")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=f"""You are a master in project management, capable of creating and managing user stories, epics, and reports. 
    You have to delegate tasks to specialized sub-agents, such as `user_stories_creator`, `epics_creator`, and `report_creator`.   
    """,
    sub_agents=[
        user_stories_creator, 
        epics_creator,
        report_creator
    ]
)
