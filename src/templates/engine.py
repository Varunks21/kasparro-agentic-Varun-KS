"""
Template Engine - Structured Definition System
==============================================
A template engine of our own design that defines:
- Fields: What data each template requires
- Rules: Validation and transformation rules
- Formatting: How data is formatted in output
- Dependencies: Which logic blocks are required

This is NOT a string templating system - it's a structured
schema-based assembly engine for machine-readable output.
"""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum

from src.models.internal import ProductData, CompetitorData
from src.models.output import ProductPage, FAQPage, ComparisonPage, ComparisonRow, FAQItem


class FieldType(Enum):
    """Types of fields in templates."""
    STRING = "string"
    NUMBER = "number"
    LIST = "list"
    OBJECT = "object"
    CURRENCY = "currency"


class TemplateField(BaseModel):
    """Definition of a single field in a template."""
    
    name: str
    field_type: FieldType
    required: bool = True
    description: str = ""
    source: Optional[str] = None  # Where to get data from (e.g., "product.name")
    transform: Optional[str] = None  # Transformation to apply
    default: Optional[Any] = None


class TemplateRule(BaseModel):
    """Validation or transformation rule for a template."""
    
    name: str
    description: str
    condition: str  # e.g., "len(benefits) >= 3"
    action: str  # e.g., "truncate", "format", "validate"


class TemplateDefinition(BaseModel):
    """
    Complete definition of a content template.
    
    This defines the structure, rules, and dependencies
    for generating a specific type of content page.
    """
    
    name: str
    description: str
    fields: List[TemplateField]
    rules: List[TemplateRule] = Field(default_factory=list)
    required_blocks: List[str] = Field(default_factory=list)  # Logic blocks needed
    output_schema: str  # Name of Pydantic model for output


# =============================================================================
# TEMPLATE DEFINITIONS
# =============================================================================

PRODUCT_PAGE_TEMPLATE = TemplateDefinition(
    name="ProductPage",
    description="Template for generating product description pages",
    fields=[
        TemplateField(
            name="title",
            field_type=FieldType.STRING,
            required=True,
            description="Product name/title",
            source="product.name"
        ),
        TemplateField(
            name="price",
            field_type=FieldType.CURRENCY,
            required=True,
            description="Formatted price with currency symbol",
            source="product.price_inr",
            transform="format_currency_inr"
        ),
        TemplateField(
            name="description",
            field_type=FieldType.STRING,
            required=True,
            description="Marketing description",
            source="generated",
            transform="combine_concentration_skintypes"
        ),
        TemplateField(
            name="key_benefits",
            field_type=FieldType.LIST,
            required=True,
            description="Marketing benefit statements",
            source="benefits_block_output"
        ),
        TemplateField(
            name="usage_guide",
            field_type=FieldType.LIST,
            required=True,
            description="Step-by-step usage instructions",
            source="usage_block_output"
        ),
        TemplateField(
            name="ingredients_list",
            field_type=FieldType.LIST,
            required=True,
            description="List of key ingredients",
            source="product.key_ingredients"
        )
    ],
    rules=[
        TemplateRule(
            name="min_benefits",
            description="Must have at least 3 benefit statements",
            condition="len(key_benefits) >= 3",
            action="validate"
        ),
        TemplateRule(
            name="price_format",
            description="Price must include rupee symbol",
            condition="price.startswith('₹')",
            action="validate"
        )
    ],
    required_blocks=["generate_benefits_block", "extract_usage_block"],
    output_schema="ProductPage"
)

FAQ_PAGE_TEMPLATE = TemplateDefinition(
    name="FAQPage",
    description="Template for generating FAQ pages with categorized Q&As",
    fields=[
        TemplateField(
            name="product_name",
            field_type=FieldType.STRING,
            required=True,
            description="Name of the product",
            source="product.name"
        ),
        TemplateField(
            name="faqs",
            field_type=FieldType.LIST,
            required=True,
            description="List of FAQ items with category, question, answer",
            source="faq_generation_output"
        )
    ],
    rules=[
        TemplateRule(
            name="min_faqs",
            description="Must have at least 5 FAQ items",
            condition="len(faqs) >= 5",
            action="validate"
        ),
        TemplateRule(
            name="categories_required",
            description="FAQs must span multiple categories",
            condition="len(set(f.category for f in faqs)) >= 3",
            action="validate"
        )
    ],
    required_blocks=[],  # Uses LLM for Q&A generation
    output_schema="FAQPage"
)

COMPARISON_PAGE_TEMPLATE = TemplateDefinition(
    name="ComparisonPage",
    description="Template for product comparison pages",
    fields=[
        TemplateField(
            name="title",
            field_type=FieldType.STRING,
            required=True,
            description="Comparison title (Product A vs Product B)",
            source="generated",
            transform="format_comparison_title"
        ),
        TemplateField(
            name="competitor_name",
            field_type=FieldType.STRING,
            required=True,
            description="Name of competitor product",
            source="competitor.name"
        ),
        TemplateField(
            name="comparison_table",
            field_type=FieldType.LIST,
            required=True,
            description="Feature-by-feature comparison rows",
            source="comparison_block_output"
        ),
        TemplateField(
            name="summary_verdict",
            field_type=FieldType.STRING,
            required=True,
            description="Summary recommendation",
            source="generated"
        )
    ],
    rules=[
        TemplateRule(
            name="min_comparisons",
            description="Must compare at least 4 features",
            condition="len(comparison_table) >= 4",
            action="validate"
        ),
        TemplateRule(
            name="has_verdict",
            description="Each row must have a verdict",
            condition="all(row.verdict for row in comparison_table)",
            action="validate"
        )
    ],
    required_blocks=["compare_products_block"],
    output_schema="ComparisonPage"
)


# =============================================================================
# TEMPLATE ENGINE
# =============================================================================

class TemplateEngine:
    """
    The Template Engine - Assembles structured output from data and logic blocks.
    
    Responsibilities:
    1. Validate input data against template requirements
    2. Apply transformation rules
    3. Invoke required logic blocks
    4. Assemble final machine-readable JSON output
    
    This engine does NOT use string interpolation - it uses
    schema-based assembly with Pydantic models for type safety.
    """
    
    # Registry of available templates
    TEMPLATES: Dict[str, TemplateDefinition] = {
        "ProductPage": PRODUCT_PAGE_TEMPLATE,
        "FAQPage": FAQ_PAGE_TEMPLATE,
        "ComparisonPage": COMPARISON_PAGE_TEMPLATE
    }
    
    @classmethod
    def get_template(cls, name: str) -> Optional[TemplateDefinition]:
        """Get a template definition by name."""
        return cls.TEMPLATES.get(name)
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """List all available template names."""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_required_blocks(cls, template_name: str) -> List[str]:
        """Get the logic blocks required by a template."""
        template = cls.get_template(template_name)
        return template.required_blocks if template else []
    
    @staticmethod
    def _format_currency_inr(amount: float) -> str:
        """Format a number as Indian Rupees."""
        return f"₹{amount}"
    
    @staticmethod
    def _validate_template(template: TemplateDefinition, data: Dict[str, Any]) -> bool:
        """Validate data against template rules."""
        # In production, this would evaluate the rule conditions
        # For now, we do basic validation
        for field in template.fields:
            if field.required and field.name not in data:
                return False
        return True

    @staticmethod
    def render_product_page(
        product: ProductData, 
        benefits_copy: List[str], 
        usage_steps: List[str]
    ) -> ProductPage:
        """
        Render the Product Page using the ProductPage template.
        
        Dependencies:
        - benefits_copy: Output from generate_benefits_block
        - usage_steps: Output from extract_usage_block
        
        Returns:
            ProductPage: Machine-readable JSON structure
        """
        # Apply template rules
        skin_types = ' & '.join(product.skin_type)
        concentration = product.concentration or 'advanced'
        
        return ProductPage(
            title=product.name,
            price=TemplateEngine._format_currency_inr(product.price_inr),
            description=f"A premium {concentration} formulation designed for {skin_types} skin types.",
            key_benefits=benefits_copy,
            usage_guide=usage_steps,
            ingredients_list=product.key_ingredients
        )

    @staticmethod
    def render_faq_page(product_name: str, qa_pairs: List[Dict]) -> FAQPage:
        """
        Render the FAQ Page using the FAQPage template.
        
        Args:
            product_name: Name of the product
            qa_pairs: List of dicts with category, question, answer
            
        Returns:
            FAQPage: Machine-readable JSON structure
        """
        # Convert dict items to proper FAQItem models
        items = []
        for item in qa_pairs:
            if isinstance(item, dict):
                items.append(FAQItem(**item))
            elif isinstance(item, FAQItem):
                items.append(item)
        
        # Validate against template rules (min 5 FAQs)
        if len(items) < 5:
            raise ValueError(f"FAQ template requires at least 5 items, got {len(items)}")
        
        return FAQPage(
            product_name=product_name,
            faqs=items
        )

    @staticmethod
    def render_comparison_page(
        product_name: str, 
        competitor_name: str, 
        comparison_data: List[Dict]
    ) -> ComparisonPage:
        """
        Render the Comparison Page using the ComparisonPage template.
        
        Dependencies:
        - comparison_data: Output from compare_products_block
        
        Returns:
            ComparisonPage: Machine-readable JSON structure
        """
        rows = [ComparisonRow(**row) for row in comparison_data]
        
        # Count wins for summary
        our_wins = sum(1 for row in rows if "Us" in row.verdict)
        
        # Generate summary verdict
        if our_wins > len(rows) // 2:
            verdict = f"{product_name} is the superior choice with advantages in {our_wins} out of {len(rows)} categories."
        else:
            verdict = f"{product_name} offers competitive value against {competitor_name}."
        
        return ComparisonPage(
            title=f"{product_name} vs {competitor_name}",
            competitor_name=competitor_name,
            comparison_table=rows,
            summary_verdict=verdict
        )
    
    @classmethod
    def describe_template(cls, name: str) -> Dict[str, Any]:
        """
        Get a human-readable description of a template.
        
        Useful for documentation and debugging.
        """
        template = cls.get_template(name)
        if not template:
            return {"error": f"Template '{name}' not found"}
            
        return {
            "name": template.name,
            "description": template.description,
            "fields": [
                {
                    "name": f.name,
                    "type": f.field_type.value,
                    "required": f.required,
                    "description": f.description
                }
                for f in template.fields
            ],
            "rules": [
                {
                    "name": r.name,
                    "description": r.description
                }
                for r in template.rules
            ],
            "required_blocks": template.required_blocks,
            "output_schema": template.output_schema
        }
