from google.adk.agents import Agent, LlmAgent, LoopAgent
from google.adk.tools import google_search
from happy_hour_finder.sub_agents.search import prompt
from happy_hour_finder.sub_agents.search.shared_libraries import types

happy_hour_search_agent = LlmAgent(
    name="google_search_agent",
    model="gemini-2.5-flash",
    instruction=prompt.GOOGLE_HAPPY_HOUR_SEARCH_AGENT_INSTR,
    description="Professional happy hour locator with Google Search capabilities",
    tools=[google_search]
)

information_check_agent = LlmAgent(
    name="information_check_agent",
    model="gemini-2.5-flash",
    instruction=prompt.INFORMATION_CHECK_AGENT_INSTR,
    description="Agent that verifies and supplements happy hour information using Google Search",
    tools=[google_search]
)

json_parser_agent = Agent(
    name="json_parser_agent",
    model="gemini-2.5-flash",
    instruction=prompt.JSON_PARSER_AGENT_INSTR,
    description="Create and persist a structured JSON representation of the happy hour data",
    output_schema=types.RestaurantList,
    output_key="itinerary",
    generate_content_config=types.json_response_config,
)

