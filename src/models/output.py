from pydantic import BaseModel
from typing import List

# --- FAQ Page Models ---
class FAQItem(BaseModel):
    category: str
    question: str
    answer: str

class FAQPage(BaseModel):
    product_name: str
    faqs: List[FAQItem]

# --- Product Page Models ---
class ProductPage(BaseModel):
    title: str
    price: str
    description: str
    key_benefits: List[str]
    usage_guide: List[str]
    ingredients_list: List[str]

# --- Comparison Page Models ---
class ComparisonRow(BaseModel):
    feature: str
    our_product: str
    competitor_product: str
    verdict: str  # e.g., "Winner: Us"

class ComparisonPage(BaseModel):
    title: str
    competitor_name: str
    comparison_table: List[ComparisonRow]
    summary_verdict: str