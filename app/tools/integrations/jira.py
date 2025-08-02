import os
import requests
import base64
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


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
