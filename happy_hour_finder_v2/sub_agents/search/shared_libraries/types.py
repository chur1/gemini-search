# types.py

from typing import List
from pydantic import BaseModel, Field

class RestaurantInfo(BaseModel):
    """Contains all the basic information about the restaurant."""
    restaurant_name: str = Field(..., description="The name of the restaurant or bar")
    website: str = Field(..., description="The website URL of the restaurant (if available)")
    phone_number: str = Field(..., description="The contact phone number of the location (if available)")
    address: str = Field(..., description="The physical address of the location (if available)")
    happy_hour_times: str = Field(..., description="The days and times the happy hour is available")

class DealItem(BaseModel):
    """Represents a single happy hour deal, for either food or a drink."""
    item: str = Field(..., description="Name or type of the special")
    price: str = Field(..., description="Price of the special")
    description: str = Field(..., description="Any additional details about the special")

class Deals(BaseModel):
    """Contains lists of all drink and food deals."""
    drinks: List[DealItem]
    food: List[DealItem]

class Source(BaseModel):
    """Represents a source URL where the information was found."""
    title: str = Field(..., description="Title of the source webpage")
    link: str = Field(..., description="URL of the source webpage")

class HappyHourSpecial(BaseModel):
    """A complete happy hour entry for a single restaurant."""
    restaurant_info: RestaurantInfo
    deals: Deals
    sources: List[Source]

class HappyHourResponse(BaseModel):
    """The root object for the API response, containing a list of all happy hour specials."""
    happy_hour_specials: List[HappyHourSpecial]