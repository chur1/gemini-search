from google.adk.agents import Agent
from google.adk.tools import google_search
from happy_hour_prod import prompt

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Professional assistant that helps users find happy hours at bars and restaurants",
    instruction=prompt.ROOT_AGENT_INSTR,
    tools=[
        google_search,    
    ]
)