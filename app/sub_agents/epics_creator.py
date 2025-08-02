from google.adk.agents import LoopAgent, Agent
from google.adk.tools.tool_context import ToolContext

STATE_CURRENT_EPIC = "current_epic"
STATE_CRITICISM = "criticism"
# Define the exact phrase the Critic should use to signal completion
COMPLETION_PHRASE = "No major issues found."

# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
  """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
  print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
  tool_context.actions.escalate = True
  # Return empty dict as tools should typically return JSON-serializable output
  return {}


# --- Agent Definitions ---

# STEP 1: Initial Epic Writer Agent (Runs ONCE at the beginning)
epics_creator = Agent(
    name="epics_creator",
    model="gemini-2.5-flash",
    instruction=f"""You are a master in project management, capable of creating epics that group related user stories. 
    You can analyze requirements and delegate tasks to specialized sub-agents, such as `epics_refiner`.
    Output *only* the epic/document text. Do not add introductions or explanations.
""",
    description="Writes the initial epic draft , aiming for some initial structure and content.",
    output_key=STATE_CURRENT_EPIC
)

# STEP 2a: Epic Critic Agent (Inside the Refinement Loop)
epics_critic_in_loop = Agent(
    name="epics_critic",
    model="gemini-2.5-flash",
    instruction=f"""You are a master in project management, capable of critically 
        reviewing epics and providing constructive feedback.

        **Epic to Review:**
        ```
        {{current_epic}}
        ```
        **Your Task:**
        Critically analyze the epic and provide feedback on its structure, clarity, and completeness.
        If you find no major issues, respond with the exact phrase: `{COMPLETION_PHRASE}`.
        Do not add explanations. Output only the critique OR the exact completion phrase.
        """,
    output_key=STATE_CRITICISM
)

# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
epic_refiner_agent_in_loop = Agent(
    name="RefinerAgent",
    model="gemini-2.5-flash",
    # Relies solely on state via placeholders
    instruction=f"""You are a Epics Writing Assistant refining an Epic based on feedback OR exiting the process.
    **Current Epic:**
    ```
    {{current_epic}}
    ```
    **Critique/Suggestions:**
    {{criticism}}

    **Task:**
    Analyze the 'Critique/Suggestions'.
    IF the critique is *exactly* "{COMPLETION_PHRASE}":
    You MUST call the 'exit_loop' function. Do not output any text.
    ELSE (the critique contains actionable feedback):
    Carefully apply the suggestions to improve the 'Current Epic'. Output *only* the refined Epic text.

    Do not add explanations. Either output the refined Epic OR call the exit_loop function.
""",
    description="Refines the Epic based on critique, or calls exit_loop if critique indicates completion.",
    tools=[exit_loop], # Provide the exit_loop tool
    output_key=STATE_CURRENT_EPIC # Overwrites state['current_epic'] with the refined version
)

# STEP 2: Refinement Loop Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    # Agent order is crucial: Critique first, then Refine/Exit
    sub_agents=[
        epics_critic_in_loop,  # Criticizes the current epic
        epic_refiner_agent_in_loop  # Refines or exits based on critique
    ],
    max_iterations=5 # Limit loops
)