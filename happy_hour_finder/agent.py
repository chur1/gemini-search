from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool  # <-- Add this import

from happy_hour_finder import prompt
from happy_hour_finder.sub_agents.search.agent import happy_hour_search_agent, information_check_agent, json_parser_agent

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Professional assistant that helps users find happy hours at bars and restaurants",
    instruction=prompt.ROOT_AGENT_INSTR,
    tools=[
        AgentTool(agent=happy_hour_search_agent),
        AgentTool(agent=information_check_agent),
        AgentTool(agent=json_parser_agent),
    ]
)