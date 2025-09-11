from pydantic import BaseModel, Field
from typing import Optional, List
from google.genai import types

# This configuration tells the model to output its response as a JSON object.
json_response_config = types.GenerateContentConfig(
    response_mime_type="application/json"
)

# --- NESTED Pydantic Models for the desired JSON structure ---

class DealItem(BaseModel):
    """Represents a single item in a list of deals."""
    item: str = Field(description="A specific food or drink item on special.")
    description: Optional[str] = Field(default=None, description="A brief description of the item.")
    price: Optional[str] = Field(default=None, description="The price of the item.")

class SpecialDeals(BaseModel):
    """Defines the structure for special deals on food and drinks."""
    food: Optional[List[DealItem]] = Field(default=None, description="A list of special food deals.")
    drinks: Optional[List[DealItem]] = Field(default=None, description="A list of special drink deals.")

class Menu(BaseModel):
    """Contains information about the restaurant's menu."""
    special_deals: SpecialDeals = Field(description="Information about special deals on the menu.")

class BasicInformation(BaseModel):
    """Contains the basic, high-level information about the restaurant."""
    restaurant_name: str = Field(description="Name of the restaurant or bar.")
    description: Optional[str] = Field(default=None, description="A brief description of the restaurant or bar.")
    address: Optional[str] = Field(default=None, description="The physical address of the establishment.")
    website: Optional[str] = Field(default=None, description="The official website URL.")
    phone_number: Optional[str] = Field(default=None, description="The contact phone number.")
    happy_hour_times: Optional[str] = Field(default=None, description="The times for happy hour specials.")

class Sources(BaseModel):
    """A list of sources used to gather information about the restaurant."""
    sources: List[str] = Field(description="A list of URLs or references where the information was obtained.")

# This is the main model you will use as the output_schema.
# I've renamed it from MenuItem for clarity, as it holds all restaurant info.
class RestaurantInfo(BaseModel):
    """Schema for restaurant information, including basic details and menu specials."""
    basic_information: BasicInformation = Field(description="Core details about the restaurant.")
    menu: Menu = Field(description="Details about the menu and special offers.")
    sources: Sources = Field(description="Sources of the information provided.")

class RestaurantList(BaseModel):
    """A list of restaurants with happy hour information."""
    restaurants: List[RestaurantInfo] = Field(description="A list of structured restaurant objects.")