from pydantic import BaseModel, Field
from typing import List, Optional

class ProductData(BaseModel):
    """
    The strictly typed internal representation of the product.
    This acts as the 'Clean Internal Model' required by the assignment.
    """
    name: str = Field(..., description="The commercial name of the product")
    concentration: Optional[str] = Field(None, description="Concentration of active ingredients")
    skin_type: List[str] = Field(..., description="List of suitable skin types")
    key_ingredients: List[str] = Field(..., description="List of active ingredients")
    benefits: List[str] = Field(..., description="List of claimed benefits")
    usage_instructions: str = Field(..., description="Raw usage text")
    side_effects: Optional[str] = Field(None, description="Potential side effects")
    price_inr: float = Field(..., description="Price in Indian Rupees")

class CompetitorData(BaseModel):
    """
    Schema for the fictional competitor (Product B).
    """
    name: str
    key_ingredients: List[str]
    price_inr: float
    pros: List[str]
    cons: List[str]