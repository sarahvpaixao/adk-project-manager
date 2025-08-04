# Project Management Agent Helper

Este projeto implementa um sistema de agentes para automação de tarefas de gerenciamento de projetos no Jira. Ele utiliza uma arquitetura com um agente raiz que coordena subagentes especializados em criar épicos, tarefas e gerar relatórios.

### Demonstração

![PM-Test GIF](https://github.com/user-attachments/assets/30a2a2a9-135a-480b-a555-4996580120ed)


## Visão Geral da Arquitetura

O sistema é composto por um `root_agent` que, com base na solicitação do usuário, delega as tarefas para os seguintes subagentes:

  * **epic\_creator**: Responsável por criar novos épicos no Jira.
  * **tasks\_creator**: Cria tarefas e as vincula a épicos existentes.
  * **report\_creator**: Gera relatórios analíticos sobre o status do projeto.

-----

## Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados:

  * Python 3.10 ou superior
  * Git
  * Make

O gerenciador de pacotes `uv` será instalado automaticamente se não for encontrado.

-----

## Configuração do Ambiente

Siga os passos abaixo para configurar o ambiente de desenvolvimento.

### 1\. Clonar o Repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd pm-agent-helper
```

### 2\. Criar e Ativar um Ambiente Virtual

É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.

  * **No macOS e Linux:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

  * **No Windows:**

    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    ```

### 3\. Instalar as Dependências

O projeto gerencia suas dependências através de um arquivo `pyproject.toml`. Para instalar todas as dependências de desenvolvimento, execute o seguinte comando:

```bash
make install
```

### 4\. Configurar as Variáveis de Ambiente

O projeto requer algumas variáveis de ambiente para se conectar ao Jira e configurar os modelos de linguagem. Crie um arquivo chamado `.env` na raiz do projeto, baseado no arquivo `app/.env`, e preencha com suas informações:

```ini
# Google Cloud
GOOGLE_CLOUD_PROJECT = "seu-gcp-project-id"

# Jira
JIRA_URL="https://seu-dominio.atlassian.net"
JIRA_EMAIL="seu-email@exemplo.com"
JIRA_API_TOKEN="seu-api-token"

# Models
ROOT_MODEL="gemini-2.5-flash"
EPIC_CREATOR_MODEL="gemini-2.5-flash"
TASK_CREATOR_MODEL="gemini-2.5-flash"
REPORT_CREATOR_MODEL="gemini-2.5-flash"
```

**Importante:** Suas credenciais do Jira são sensíveis. Não as exponha publicamente.

-----

## Executando o Agente

### Execução Local (Playground)

Para iniciar o ambiente de desenvolvimento local e interagir com o agente através de uma interface web, execute:

```bash
make playground
```
-----

## Exemplos de Prompts para Teste

Ao executar o `playground`, você pode usar os seguintes exemplos de prompts para testar as capacidades do agente:

### Para Criar um Épico

Use este prompt para testar o `epic_creator`.

> "Quero criar um épico para a nova funcionalidade de 'Pagamento via Pix'. A descrição deve incluir os seguintes requisitos: integração com a API do banco, geração de QR Code, confirmação de pagamento em tempo real e notificação ao usuário após a confirmação."

### Para Criar Tarefas

Este prompt testa o `tasks_creator`. Para um melhor resultado, use-o após a criação de um épico.

> "Para o épico de 'Pagamento via Pix', crie as seguintes tarefas: 'Desenvolver a interface de seleção de Pix', 'Implementar a chamada para a API do banco para gerar o QR Code' e 'Criar o serviço de webhook para receber a confirmação de pagamento'."

### Para Atualizar um Issue

Este prompt testa a funcionalidade do `issue_updater`.

> "Preciso atualizar o issue ADK-18. Por favor, altere o título para 'Implementação Final da API de Pagamentos' e atualize a descrição para 'A nova descrição deve refletir a conclusão dos testes de integração'."

### Para Gerar um Relatório

Teste o `report_creator` com um prompt como este:

> "Gere um relatório de progresso do projeto. Quero ver a quantidade total de épicos e tarefas, a distribuição de tarefas por status (To Do, In Progress, Done) e a taxa de conclusão de cada épico."

### Para um Fluxo Completo (Agente Raiz)

Este prompt testa a capacidade do `root_agent` de coordenar múltiplos subagentes em sequência.

> "Vamos iniciar a funcionalidade de 'Dashboard de Vendas'. Primeiro, crie um épico com este nome. A descrição deve mencionar que o dashboard exibirá métricas de vendas diárias, semanais e mensais. Depois, adicione as seguintes tarefas a este épico: 'Desenvolver o layout do dashboard', 'Criar os endpoints da API para as métricas' e 'Integrar o frontend com a API'."
