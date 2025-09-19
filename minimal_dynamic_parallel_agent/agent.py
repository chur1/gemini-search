import random, secrets, json
from typing import ClassVar, List
from google.adk.events import Event, EventActions
from google.adk.agents import BaseAgent, ParallelAgent, SequentialAgent, Agent
from google.adk.tools.google_search_tool import google_search
from google.genai import types

class Worker(BaseAgent):
    """Worker that searches for happy hour menus at restaurants."""
    def __init__(self, *, name: str, run_id: str):
        super().__init__(name=name)
        self._run_id = run_id
        
    async def _run_async_impl(self, ctx):
        # Get the actual restaurant name from state
        restaurant_name = ctx.session.state.get(f"restaurant:{self._run_id}:{self.name}")
        if not restaurant_name:
            error_msg = f"No restaurant assigned to worker {self.name}"
            yield Event(
                author=self.name,
                content=types.Content(
                    role=self.name,
                    parts=[types.Part(text=error_msg)]
                ),
                actions=EventActions(
                    state_delta={f"happy_hour_result:{self._run_id}:{self.name}": error_msg}
                )
            )
            return
        
        json_schema = """
        {
            "restaurant_info": {
                "restaurant_name": "string",
                "website": "string",
                "phone_number": "string",
                "address": "string",
                "happy_hour_times": "string"
            },
            "deals": { "drinks": [], "food": [] },
            "sources": []
        }
        """
        
        # Create a search agent with google_search tool
        search_agent = Agent(
            name=f"search_agent_{self._run_id}",
            model="gemini-2.5-pro",
            tools=[google_search],
            instruction=f"""
            Search for the official website of {restaurant_name} in New York and find their happy hour menu.
            Look specifically for:
                - Restaurant Name
                - Website URL (if available)
                - Phone Number (if available)
                - Address (if available)
                - Happy Hour Times (days and times the happy hour is available)
                - Deals:
                    - Drinks: List of drink specials including item name, price, and description
                    - Food: List of food specials including item name, price, and description
                - Sources: List of URLs where the information was found, including title and link
            
            Focus on finding information from the restaurant's official website or verified sources.
            Provide response in the following JSON format:
            {json_schema}
            """
        )
        
        # # Execute the search
        # search_query = f"{restaurant_name} happy hour menu official website"
        
        try:
            # Run the search agent and get the raw text output
            raw_result = ""
            async for event in search_agent.run_async(ctx):
                if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            raw_result = part.text
            
            # Attempt to parse the text as JSON
            try:
                # Clean up potential markdown formatting from the LLM
                if raw_result.strip().startswith("```json"):
                    raw_result = raw_result.strip()[7:-4]
                
                json_result = json.loads(raw_result)
                final_result = json_result
                
            except json.JSONDecodeError:
                error_msg = f"Error: Failed to decode JSON from the model's response for {restaurant_name}."
                final_result = {"error": error_msg, "response": raw_result}

            yield Event(
                author=self.name,
                # ADD THIS CONTENT SECTION:
                content=types.Content(
                    parts=[
                        types.Part(text=f"Found result for {restaurant_name}:"),
                        types.Part(text=json.dumps(final_result, indent=2))
                    ]
                ),
                actions=EventActions(
                    state_delta={f"happy_hour_result:{self._run_id}:{self.name}": final_result}
                )
            )
            
        except Exception as e:
            error_msg = f"Error searching for {restaurant_name} happy hour: {str(e)}"
            yield Event(
                author=self.name,
                content=types.Content(
                    role=self.name,
                    parts=[types.Part(text=error_msg)]
                ),
                actions=EventActions(
                    state_delta={f"happy_hour_result:{self._run_id}:{self.name}": error_msg}
                )
            )

class RestaurantFinder(BaseAgent):
    """
    Searches online sources for a list of restaurants known for happy hours
    and places the list into the shared state.
    """
    async def _run_async_impl(self, ctx):
        run_id = secrets.token_hex(2)
        
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Searching for restaurants with happy hours in NYC...")])
        )
        
        # This agent is specialized to find and list restaurants
        search_agent = Agent(
            name=f"restaurant_lister_{run_id}",
            model="gemini-1.5-pro", # Use a powerful model for good extraction
            tools=[google_search],
            instruction="""
            Search online for blog posts and articles listing restaurants with great happy hours in the financial district of New York Manhattan.
            From your search results, compile a list of restaurant names.
            Your final output should ONLY be a comma-separated list of the restaurant names you found.
            For example: 'Restaurant A, Restaurant B, Restaurant C'
            """
        )
        
        # Extract the final result (the comma-separated string)
        final_result_text = ""
        async for event in search_agent.run_async(ctx):
            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_result_text = part.text
        
        # Convert the string to a clean Python list
        restaurant_list = [name.strip() for name in final_result_text.split(',')]
        
        # Put the run_id and the discovered list into the state for the next agent
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Found restaurants: {restaurant_list}")]),
            actions=EventActions(state_delta={
                "current_run": run_id, # Set the run_id for the whole sequence
                f"restaurant_list:{run_id}": restaurant_list
            })
        )

class PlannerAndRunner(BaseAgent):
    """
    Reads a restaurant list from the state, distributes tasks,
    and dynamically creates a ParallelAgent.
    """
    # The hard-coded list is now removed!
    # RESTAURANTS: ClassVar[List[str]] = ["Carne Mare", "The Full Shilling", "The Continental Bar"]
    
    async def _run_async_impl(self, ctx):
        # 1. Get the run_id and restaurant list from the state
        run_id = ctx.session.state.get("current_run")
        if not run_id:
            # Handle error if the finder agent failed
            yield Event(author=self.name, content=types.Content(parts=[types.Part(text="Error: No run_id found from finder.")]))
            return
            
        picked = ctx.session.state.get(f"restaurant_list:{run_id}", [])
        if not picked:
            # Handle error if the list is empty
            yield Event(author=self.name, content=types.Content(parts=[types.Part(text="Error: No restaurants found to plan for.")]))
            return

        # --- The rest of the logic is nearly identical ---
        
        # Create valid agent names and store restaurant mapping
        restaurant_mapping = {}
        valid_workers = []
        
        for i, restaurant in enumerate(picked):
            valid_name = f"worker_{run_id}_{i}"
            restaurant_mapping[valid_name] = restaurant
            valid_workers.append(valid_name)
        
        task_delta = {f"task:{run_id}:{name}": random.randint(1, 9)
                      for name in valid_workers}
        
        # Store restaurant mapping in state
        restaurant_state = {f"restaurant:{run_id}:{name}": restaurant 
                           for name, restaurant in restaurant_mapping.items()}
        
        yield Event(
            author=self.name,
            content=types.Content(role=self.name,
                parts=[types.Part(text=f"Run {run_id} tasks for dynamically found restaurants: {picked}")]),
            actions=EventActions(state_delta={
                f"workers:{run_id}": valid_workers,
                **task_delta, 
                **restaurant_state
            })
        )
        
        parallel = ParallelAgent(
            name=f"block_{run_id}",
            sub_agents=[Worker(name=n, run_id=run_id) for n in valid_workers]
        )
        async for ev in parallel.run_async(ctx):
            yield ev

class Aggregator(BaseAgent):
    """Aggregates happy hour search results from restaurant workers."""
    async def _run_async_impl(self, ctx):
        run_id = ctx.session.state.get("current_run")
        if not run_id:
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text="Error: No run_id found.")]))
            return

        # 1. Directly get the list of workers for this run
        worker_list = ctx.session.state.get(f"workers:{run_id}", [])
        
        # This will be a list of JSON objects
        happy_hour_results = []
        
        for worker_name in worker_list:
            result = ctx.session.state.get(f"happy_hour_result:{run_id}:{worker_name}")
            
            # Append the result if it's a valid dictionary (not None or an error string)
            if isinstance(result, dict) and "error" not in result:
                happy_hour_results.append(result)

        # Create the final JSON structure
        final_json_output = {"happy_hour_specials": happy_hour_results}
        
        yield Event(
            author=self.name,
            # We now output the final JSON as a string for display/storage
            content=types.Content(role=self.name, parts=[types.Part(text=json.dumps(final_json_output, indent=4))]),
            actions=EventActions(
                escalate=True, 
                state_delta={f"aggregated_summary:{run_id}": final_json_output}
            )
        )

root_agent = SequentialAgent(
    name="root",
    sub_agents=[
        RestaurantFinder(name="finder"),  # <-- Step 1: Find the restaurants
        PlannerAndRunner(name="planner"), # <-- Step 2: Plan and run workers
        Aggregator(name="collector")       # <-- Step 3: Collect the results
    ]
)