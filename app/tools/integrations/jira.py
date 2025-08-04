import os
import requests
import base64
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class JiraConfig:
    """Configuration class for Jira API connection.
    
    This class encapsulates all necessary configuration parameters
    for establishing connection with Jira API.
    
    Attributes:
        url: Base URL of the Jira instance.
        email: User email for authentication.
        api_token: API token for authentication.
        epic_name_field_id: Custom field ID for epic name.
    """
    url: str
    email: str
    api_token: str
    epic_name_field_id: str = "customfield_10040"


class JiraClient:
    """HTTP client for Jira API operations.
    
    This class provides a reusable HTTP client for making requests to Jira API.
    It handles authentication, request formatting, and error handling in a 
    centralized manner following the Single Responsibility Principle.
    
    The client supports creating various issue types and can be easily extended
    for additional Jira operations while maintaining consistent error handling
    and authentication patterns.
    """
    
    def __init__(self, config: Optional[JiraConfig] = None) -> None:
        """Initialize Jira client with configuration.
        
        Args:
            config: Jira configuration object. If None, loads from environment variables.
            
        Raises:
            ValueError: When required environment variables are missing.
        """
        self.config = config or self._load_config_from_env()
        self.headers = self._build_headers()
    
    def _load_config_from_env(self) -> JiraConfig:
        """Load Jira configuration from environment variables.
        
        Returns:
            JiraConfig object with loaded configuration.
            
        Raises:
            ValueError: When required environment variables are missing.
        """
        try:
            return JiraConfig(
                url=os.environ['JIRA_URL'],
                email=os.environ['JIRA_EMAIL'],
                api_token=os.environ['JIRA_API_TOKEN']
            )
        except KeyError as e:
            raise ValueError(f"Required environment variable {e} is not defined")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for Jira API requests.
        
        Creates authentication headers using Basic Auth with base64 encoding
        of email and API token combination.
        
        Returns:
            Dictionary containing HTTP headers for API requests.
        """
        auth_string = f"{self.config.email}:{self.config.api_token}"
        base64_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64_auth}"
        }
    
    def create_issue(self, payload: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
        """Create a new issue in Jira.
        
        Sends a POST request to Jira API to create a new issue with the provided
        payload. Handles HTTP errors and provides detailed error messages.
        
        Args:
            payload: Issue creation payload following Jira API format.
            timeout: Request timeout in seconds.
            
        Returns:
            Dictionary containing the API response with issue details.
            
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        api_endpoint = f"{self.config.url}/rest/api/2/issue"
        
        response = requests.post(
            api_endpoint, 
            data=json.dumps(payload), 
            headers=self.headers, 
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    
    def create_epic(self, summary: str, description: str, project_key: str) -> Dict[str, Any]:
        """Create an Epic issue in Jira.
        
        Constructs the payload for Epic creation and delegates to create_issue method.
        Epic is a special issue type that groups related stories and tasks.
        
        Args:
            summary: Epic title or summary.
            description: Detailed description of the epic.
            project_key: Jira project key (e.g., 'ADK').
            
        Returns:
            Dictionary containing the created epic details.
            
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Epic"},
                self.config.epic_name_field_id: summary
            }
        }
        
        return self.create_issue(payload)
    
    def search_epics(self, project_key: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for epic issues in a Jira project.
        
        Executes a JQL (Jira Query Language) search to retrieve all epics
        from the specified project. Returns essential epic information
        including key, summary, description, and epic name.
        
        Args:
            project_key: Jira project key to search epics from.
            max_results: Maximum number of epics to retrieve.
            
        Returns:
            List of dictionaries containing epic information with keys:
                - key: Issue key (e.g., 'ADK-123')
                - summary: Epic title
                - description: Epic description text
                - epic_name: Epic name from custom field
                
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        api_endpoint = f"{self.config.url}/rest/api/2/search"
        
        jql = f'project = "{project_key}" AND issuetype = Epic ORDER BY created DESC'
        
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": f"key,summary,description,{self.config.epic_name_field_id}"
        }
        
        response = requests.get(
            api_endpoint,
            headers=self.headers,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        epics = []
        
        for issue in data.get("issues", []):
            fields = issue.get("fields", {})
            epic_info = {
                "key": issue.get("key", ""),
                "summary": fields.get("summary", ""),
                "description": fields.get("description", ""),
                "epic_name": fields.get(self.config.epic_name_field_id, "")
            }
            epics.append(epic_info)
        
        return epics
    
    def create_task(self, summary: str, description: str, project_key: str, 
                   epic_key: Optional[str] = None) -> Dict[str, Any]:
        """Create a Task issue in Jira.
        
        Creates a task issue type in Jira with optional epic linkage.
        Tasks represent individual work items that can be linked to epics
        for better organization and tracking.
        
        Args:
            summary: Task title or summary.
            description: Detailed description of the task.
            project_key: Jira project key (e.g., 'ADK').
            epic_key: Optional epic key to link the task to.
            
        Returns:
            Dictionary containing the created task details.
            
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        # First, try to determine the correct task type name
        try:
            available_types = self.get_available_issue_types(project_key)
            
            # Common task type names in different languages
            task_type_candidates = ["Task", "Tarefa", "Tarea", "Aufgabe", "Story", "História"]
            
            # Find the first matching task type
            task_type = None
            for candidate in task_type_candidates:
                if candidate in available_types:
                    task_type = candidate
                    break
            
            # If no common task type found, use any non-epic, non-subtask type
            if not task_type:
                for issue_type in available_types:
                    if issue_type.lower() not in ["epic", "sub-task", "subtask", "subtarefa"]:
                        task_type = issue_type
                        break
            
            if not task_type:
                task_type = "Task"  # Fallback
                
        except Exception:
            task_type = "Task"  # Default fallback
        
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": task_type}
            }
        }
        
        if epic_key:
            payload["fields"]["parent"] = {"key": epic_key}
        
        return self.create_issue(payload)
    
    def get_available_issue_types(self, project_key: str) -> List[str]:
        """Get available issue types for a project.
        
        Retrieves all issue types configured for the specified project,
        allowing dynamic adaptation to different Jira configurations.
        
        Args:
            project_key: Jira project key to check.
            
        Returns:
            List of available issue type names.
            
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        api_endpoint = f"{self.config.url}/rest/api/2/project/{project_key}"
        
        response = requests.get(
            api_endpoint,
            headers=self.headers,
            timeout=15
        )
        response.raise_for_status()
        
        project_data = response.json()
        issue_types = []
        
        for issue_type in project_data.get("issueTypes", []):
            issue_types.append(issue_type["name"])
        
        return issue_types
    
    def get_project_status(self, project_key: str, days_back: int = 7) -> Dict[str, Any]:
        """Get comprehensive project status including epics and tasks.
        
        Retrieves detailed project information including all epics and their
        associated tasks, with status breakdown and progress metrics.
        
        Args:
            project_key: Jira project key to analyze.
            days_back: Number of days to look back for recent activity.
            
        Returns:
            Dictionary containing project status with structure:
                - total_epics: Total number of epics
                - total_tasks: Total number of tasks
                - tasks_by_status: Task count grouped by status
                - epics_detail: List of epics with their task details
                - recent_updates: Recently updated items
                
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        api_endpoint = f"{self.config.url}/rest/api/2/search"
        
        # First, get available issue types
        try:
            available_types = self.get_available_issue_types(project_key)
            
            # Filter for task-like issue types (exclude Epic and Sub-task)
            task_types = [t for t in available_types 
                         if t not in ["Epic", "Sub-task"] 
                         and t.lower() not in ["epic", "sub-task"]]
            
            # Build JQL for task types
            if task_types:
                task_type_list = ", ".join([f'"{t}"' for t in task_types])
                task_jql = f'project = "{project_key}" AND issuetype in ({task_type_list})'
            else:
                # Fallback to all non-epic issues
                task_jql = f'project = "{project_key}" AND issuetype != Epic'
                
        except Exception:
            # If we can't get issue types, use a more generic query
            task_jql = f'project = "{project_key}" AND issuetype != Epic'
        
        # Get all epics with their linked issues
        epic_jql = f'project = "{project_key}" AND issuetype = Epic'
        
        epic_params = {
            "jql": epic_jql,
            "maxResults": 100,
            "fields": "key,summary,description,status"
        }
        
        epic_response = requests.get(
            api_endpoint,
            headers=self.headers,
            params=epic_params,
            timeout=15
        )
        epic_response.raise_for_status()
        epic_data = epic_response.json()
        
        # Get all tasks
        task_params = {
            "jql": task_jql,
            "maxResults": 500,
            "fields": "key,summary,status,parent,updated,issuetype"
        }
        
        task_response = requests.get(
            api_endpoint,
            headers=self.headers,
            params=task_params,
            timeout=15
        )
        task_response.raise_for_status()
        task_data = task_response.json()
        
        # Process the data
        epics = []
        epic_map = {}
        
        for epic in epic_data.get("issues", []):
            epic_info = {
                "key": epic["key"],
                "summary": epic["fields"]["summary"],
                "status": epic["fields"]["status"]["name"],
                "tasks": [],
                "task_count": 0,
                "completed_tasks": 0
            }
            epics.append(epic_info)
            epic_map[epic["key"]] = epic_info
        
        # Group tasks by status and type
        tasks_by_status = {}
        tasks_by_type = {}
        total_tasks = 0
        recent_updates = []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for task in task_data.get("issues", []):
            total_tasks += 1
            status = task["fields"]["status"]["name"]
            issue_type = task["fields"]["issuetype"]["name"]
            
            tasks_by_status[status] = tasks_by_status.get(status, 0) + 1
            tasks_by_type[issue_type] = tasks_by_type.get(issue_type, 0) + 1
            
            # Check if task belongs to an epic
            parent = task["fields"].get("parent")
            if parent and parent["key"] in epic_map:
                task_info = {
                    "key": task["key"],
                    "summary": task["fields"]["summary"],
                    "status": status,
                    "type": issue_type
                }
                epic_map[parent["key"]]["tasks"].append(task_info)
                epic_map[parent["key"]]["task_count"] += 1
                
                if status.lower() in ["done", "closed", "resolved", "concluído", "fechado"]:
                    epic_map[parent["key"]]["completed_tasks"] += 1
            
            # Check for recent updates
            updated = task["fields"].get("updated")
            if updated:
                try:
                    updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    if updated_date.replace(tzinfo=None) > cutoff_date:
                        recent_updates.append({
                            "key": task["key"],
                            "summary": task["fields"]["summary"],
                            "updated": updated,
                            "status": status,
                            "type": issue_type
                        })
                except Exception:
                    pass
        
        # Calculate completion rates for epics
        for epic in epics:
            if epic["task_count"] > 0:
                epic["completion_rate"] = round(
                    (epic["completed_tasks"] / epic["task_count"]) * 100, 1
                )
            else:
                epic["completion_rate"] = 0
        
        return {
            "total_epics": len(epics),
            "total_tasks": total_tasks,
            "tasks_by_status": tasks_by_status,
            "tasks_by_type": tasks_by_type,
            "epics_detail": epics,
            "recent_updates": sorted(
                recent_updates, 
                key=lambda x: x["updated"], 
                reverse=True
            )[:10] if recent_updates else []
        }
    
    def update_issue(self, issue_key: str, fields: Dict[str, Any], timeout: int = 15) -> None:
        """Update an existing issue in Jira.
        
        Sends a PUT request to the Jira API to update an issue with the
        provided fields.
        
        Args:
            issue_key: The key of the issue to update (e.g., 'ADK-123').
            fields: Dictionary containing the fields to update.
            timeout: Request timeout in seconds.
            
        Raises:
            requests.exceptions.RequestException: When API request fails.
        """
        api_endpoint = f"{self.config.url}/rest/api/2/issue/{issue_key}"
        payload = {"fields": fields}
        response = requests.put(
            api_endpoint, 
            data=json.dumps(payload), 
            headers=self.headers, 
            timeout=timeout
        )
        response.raise_for_status()


def create_jira_epic(summary: str, description: str, project_key: str) -> str:
    """Create an Epic issue in Jira using the JiraClient.
    
    This function serves as the tool interface for Google Agent ADK while
    leveraging the JiraClient class for actual API communication. It provides
    a clean separation between the tool interface and the HTTP client logic.
    
    The function handles all error scenarios gracefully and provides user-friendly
    messages for both success and failure cases. It maintains backward compatibility
    with existing ADK agent implementations.
    
    Args:
        summary: The title or summary of the epic.
        description: The detailed description of the epic.
        project_key: The key of the Jira project (e.g., 'ADK').
        
    Returns:
        Success message with issue key or detailed error message.
        
    Example:
        >>> result = create_jira_epic("New Feature", "Implement new functionality", "ADK")
        >>> print(result)
        "Épico foi criado com sucesso no Jira com a chave: ADK-123"
    """
    print(f"[Tool Call] create_jira_epic: Criando épico '{summary}' no projeto '{project_key}'...")
    
    try:
        client = JiraClient()
        response = client.create_epic(summary, description, project_key)
        issue_key = response['key']
        
        print(f"    [Tool Success] Épico criado com sucesso! Chave: {issue_key}")
        return f"Épico foi criado com sucesso no Jira com a chave: {issue_key}"
        
    except ValueError as e:
        error_message = f"Erro de configuração: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except requests.exceptions.RequestException as e:
        error_response_text = "Nenhuma resposta detalhada recebida."
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_response_text = json.dumps(
                    e.response.json(), 
                    indent=4, 
                    ensure_ascii=False
                )
            except json.JSONDecodeError:
                error_response_text = e.response.text
        
        error_message = f"Erro ao chamar a API do Jira: {e}. Resposta detalhada:\n{error_response_text}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except Exception as e:
        error_message = f"Erro inesperado: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message

def get_jira_epics(project_key: str) -> str:
    """Retrieve all epics from a Jira project.
    
    This function serves as the tool interface for Google Agent ADK to fetch
    existing epics from a Jira project. It formats the epic information in a
    structured way that can be easily parsed and used by agents for creating
    related tasks.
    
    The function returns a formatted string containing all epics with their
    key, summary, and description, making it easy for agents to reference
    specific epics when creating tasks.
    
    Args:
        project_key: The key of the Jira project (e.g., 'ADK').
        
    Returns:
        Formatted string containing epic information or error message.
        
    Example:
        >>> result = get_jira_epics("ADK")
        >>> print(result)
        "Épicos encontrados no projeto ADK:\\n\\n[ADK-123] New Feature Epic..."
    """
    print(f"[Tool Call] get_jira_epics: Buscando épicos do projeto '{project_key}'...")
    
    try:
        client = JiraClient()
        epics = client.search_epics(project_key)
        
        if not epics:
            message = f"Nenhum épico encontrado no projeto {project_key}"
            print(f"    [Tool Info] {message}")
            return message
        
        formatted_epics = f"Épicos encontrados no projeto {project_key}:\n\n"
        
        for epic in epics:
            formatted_epics += f"[{epic['key']}] {epic['summary']}\n"
            if epic['description']:
                formatted_epics += f"Descrição: {epic['description'][:200]}...\n"
            formatted_epics += "\n"
        
        print(f"    [Tool Success] {len(epics)} épicos encontrados")
        return formatted_epics
        
    except ValueError as e:
        error_message = f"Erro de configuração: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except requests.exceptions.RequestException as e:
        error_response_text = "Nenhuma resposta detalhada recebida."
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_response_text = json.dumps(
                    e.response.json(), 
                    indent=4, 
                    ensure_ascii=False
                )
            except json.JSONDecodeError:
                error_response_text = e.response.text
        
        error_message = f"Erro ao chamar a API do Jira: {e}. Resposta detalhada:\n{error_response_text}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except Exception as e:
        error_message = f"Erro inesperado: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message

def create_jira_task(summary: str, description: str, project_key: str, 
                    epic_key: Optional[str] = None) -> str:
    """Create a Task issue in Jira with optional epic linkage.
    
    This function serves as the tool interface for Google Agent ADK to create
    tasks in Jira. It supports linking tasks to existing epics, enabling
    proper task organization within the project hierarchy.
    
    The function provides clear feedback about task creation success or failure,
    including the epic linkage status when applicable.
    
    Args:
        summary: The title or summary of the task.
        description: The detailed description of the task.
        project_key: The key of the Jira project (e.g., 'ADK').
        epic_key: Optional epic key to link the task to (e.g., 'ADK-123').
        
    Returns:
        Success message with issue key or detailed error message.
        
    Example:
        >>> result = create_jira_task("Implement login", "Add user authentication", "ADK", "ADK-123")
        >>> print(result)
        "Task foi criada com sucesso no Jira com a chave: ADK-124 (vinculada ao épico ADK-123)"
    """
    print(f"[Tool Call] create_jira_task: Criando task '{summary}' no projeto '{project_key}'...")
    if epic_key:
        print(f"    [Tool Info] Vinculando ao épico: {epic_key}")
    
    try:
        client = JiraClient()
        response = client.create_task(summary, description, project_key, epic_key)
        issue_key = response['key']
        
        success_message = f"Task foi criada com sucesso no Jira com a chave: {issue_key}"
        if epic_key:
            success_message += f" (vinculada ao épico {epic_key})"
        
        print(f"    [Tool Success] Task criada com sucesso! Chave: {issue_key}")
        return success_message
        
    except ValueError as e:
        error_message = f"Erro de configuração: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except requests.exceptions.RequestException as e:
        error_response_text = "Nenhuma resposta detalhada recebida."
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_response_text = json.dumps(
                    e.response.json(), 
                    indent=4, 
                    ensure_ascii=False
                )
            except json.JSONDecodeError:
                error_response_text = e.response.text
        
        error_message = f"Erro ao chamar a API do Jira: {e}. Resposta detalhada:\n{error_response_text}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except Exception as e:
        error_message = f"Erro inesperado: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message

def get_jira_project_status(project_key: str, days_back: int = 7) -> str:
    """Get comprehensive project status report from Jira.
    
    This function serves as the tool interface for Google Agent ADK to retrieve
    detailed project status information including epics, tasks, and recent updates.
    It provides analytics-focused data that can be used by agents to generate
    insightful reports for project managers.
    
    The function returns formatted project metrics including completion rates,
    task distribution, and recent activity, enabling data-driven decision making.
    
    Args:
        project_key: The key of the Jira project (e.g., 'ADK').
        days_back: Number of days to look back for recent updates (default: 7).
        
    Returns:
        Formatted string containing project status metrics or error message.
        
    Example:
        >>> result = get_jira_project_status("ADK", 7)
        >>> print(result)
        "Project Status Report for ADK:\\n\\nTotal Epics: 5..."
    """
    print(f"[Tool Call] get_jira_project_status: Analisando status do projeto '{project_key}'...")
    
    try:
        client = JiraClient()
        status_data = client.get_project_status(project_key, days_back)
        
        # Format the report
        report = f"Project Status Report for {project_key}\n"
        report += f"{'=' * 50}\n\n"
        
        # Summary section
        report += "📊 PROJECT SUMMARY\n"
        report += f"Total Epics: {status_data['total_epics']}\n"
        report += f"Total Tasks: {status_data['total_tasks']}\n\n"
        
        # Task distribution by status
        if status_data.get('tasks_by_status'):
            report += "📈 TASK DISTRIBUTION BY STATUS\n"
            for status, count in status_data['tasks_by_status'].items():
                percentage = (count / status_data['total_tasks'] * 100) if status_data['total_tasks'] > 0 else 0
                report += f"  • {status}: {count} ({percentage:.1f}%)\n"
            report += "\n"
        
        # Task distribution by type
        if status_data.get('tasks_by_type'):
            report += "📋 TASK DISTRIBUTION BY TYPE\n"
            for issue_type, count in status_data['tasks_by_type'].items():
                percentage = (count / status_data['total_tasks'] * 100) if status_data['total_tasks'] > 0 else 0
                report += f"  • {issue_type}: {count} ({percentage:.1f}%)\n"
            report += "\n"
        
        # Epic details
        report += f"📋 EPIC DETAILS\n"
        if status_data['epics_detail']:
            for epic in status_data['epics_detail']:
                report += f"\n[{epic['key']}] {epic['summary']}\n"
                report += f"  Status: {epic['status']}\n"
                report += f"  Tasks: {epic['task_count']} (Completion: {epic['completion_rate']}%)\n"
                
                if epic['tasks']:
                    report += "  Task breakdown:\n"
                    status_counts = {}
                    for task in epic['tasks']:
                        status_counts[task['status']] = status_counts.get(task['status'], 0) + 1
                    
                    for status, count in status_counts.items():
                        report += f"    - {status}: {count}\n"
        else:
            report += "  No epics found in the project.\n"
        
        # Recent updates
        report += f"\n🔄 RECENT UPDATES (Last {days_back} days)\n"
        if status_data['recent_updates']:
            for item in status_data['recent_updates'][:5]:
                item_type = item.get('type', 'Unknown')
                report += f"  • [{item['key']}] {item['summary']} ({item_type}) - {item['status']}\n"
        else:
            report += "  No recent updates\n"
        
        print(f"    [Tool Success] Status report generated successfully")
        return report
        
    except ValueError as e:
        error_message = f"Erro de configuração: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except requests.exceptions.RequestException as e:
        error_response_text = "Nenhuma resposta detalhada recebida."
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_response_text = json.dumps(
                    error_details, 
                    indent=4, 
                    ensure_ascii=False
                )
                
                # Check for specific error about issue types
                if "issuetype" in str(error_details).lower():
                    error_response_text += "\n\nNOTA: Parece que há um problema com os tipos de issues no projeto. O sistema tentará adaptar-se automaticamente aos tipos disponíveis."
                    
            except json.JSONDecodeError:
                error_response_text = e.response.text
        
        error_message = f"Erro ao chamar a API do Jira: {e}. Resposta detalhada:\n{error_response_text}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except Exception as e:
        error_message = f"Erro inesperado: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message

def update_jira_issue(issue_key: str, summary: Optional[str] = None, description: Optional[str] = None) -> str:
    """Update an existing issue in Jira (summary or description).
    
    This tool allows updating the summary and/or description of a specific
    Jira issue.
    
    Args:
        issue_key: The key of the issue to update (e.g., 'ADK-123').
        summary: The new summary (title) for the issue.
        description: The new detailed description for the issue.
        
    Returns:
        A success or error message.
    """
    print(f"[Tool Call] update_jira_issue: Atualizando issue '{issue_key}'...")
    
    fields_to_update = {}
    if summary:
        fields_to_update["summary"] = summary
    if description:
        fields_to_update["description"] = description
        
    if not fields_to_update:
        return "Erro: Nenhum campo para atualizar foi fornecido. Você deve fornecer um 'summary' ou 'description'."

    try:
        client = JiraClient()
        client.update_issue(issue_key, fields_to_update)
        
        success_message = f"Issue {issue_key} foi atualizado com sucesso."
        print(f"    [Tool Success] {success_message}")
        return success_message
        
    except ValueError as e:
        error_message = f"Erro de configuração: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except requests.exceptions.RequestException as e:
        error_response_text = "Nenhuma resposta detalhada recebida."
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_response_text = json.dumps(
                    e.response.json(), 
                    indent=4, 
                    ensure_ascii=False
                )
            except json.JSONDecodeError:
                error_response_text = e.response.text
        
        error_message = f"Erro ao chamar a API do Jira: {e}. Resposta detalhada:\n{error_response_text}"
        print(f"    [Tool Error] {error_message}")
        return error_message
        
    except Exception as e:
        error_message = f"Erro inesperado: {e}"
        print(f"    [Tool Error] {error_message}")
        return error_message