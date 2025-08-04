"""Tools registration module for Google ADK agents.

This module demonstrates how to properly register the Jira integration tools
for use with Google ADK agents. Each tool function is imported from the main
Jira client module and can be assigned to agents as needed.

The tools follow the ADK pattern where they accept parameters and return
string responses that agents can parse and use for decision making.
"""

from .integrations.jira import (
    create_jira_epic,
    get_jira_epics,
    create_jira_task,
    get_jira_project_status,
    update_jira_issue
)

__all__ = [
    'create_jira_epic',
    'get_jira_epics', 
    'create_jira_task',
    'get_jira_project_status',
    'update_jira_issue'
]
