from google.adk.agents import Agent
from google.adk.tools import google_search
from happy_hour_finder_v2 import prompt
from happy_hour_finder_v2.shared_libraries import types

root_agent = Agent(
    model="gemini-2.5-pro",
    name="root_agent",
    description="Professional assistant that helps users find happy hours at bars and restaurants",
    instruction=prompt.ROOT_AGENT_INSTR,
    tools=[google_search]
)