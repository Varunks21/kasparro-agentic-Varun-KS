from pydantic import BaseModel
from src.models.internal import ProductData, CompetitorData
from src.models.output import FAQPage, ProductPage, ComparisonPage, FAQItem, ComparisonRow
from src.utils.llm_client import get_structured_data
from src.utils.logger import builder_logger, log_agent_thought

# Import Logic Blocks
from src.blocks.benefits import generate_benefits_block
from src.blocks.usage import extract_usage_block
from src.blocks.comparison import compare_products_block


class BuilderAgent:
    def __init__(self):
        builder_logger.debug("BuilderAgent initialized")

    def build_product_page(self, product: ProductData) -> ProductPage:
        log_agent_thought("BuilderAgent", "Assembling Product Page", {
            "product": product.name,
            "components": "benefits, usage guide, ingredients"
        })
        
        # 1. Run Logic Blocks
        builder_logger.debug("Running BenefitsBlock...")
        marketing_copy = generate_benefits_block(product.key_ingredients, product.benefits)
        builder_logger.debug(f"  └─ Generated {len(marketing_copy)} benefit statements")
        
        builder_logger.debug("Running UsageBlock...")
        usage_steps = extract_usage_block(product.usage_instructions)
        builder_logger.debug(f"  └─ Extracted {len(usage_steps)} usage steps")
        
        # 2. Assemble with accurate data
        skin_types = ', '.join(product.skin_type)
        
        page = ProductPage(
            title=product.name,
            price=f"₹{product.price_inr}",
            description=f"A premium {product.concentration} formulation designed for {skin_types} skin types.",
            key_benefits=marketing_copy,
            usage_guide=usage_steps,
            ingredients_list=product.key_ingredients
        )
        
        builder_logger.info(f"✓ Product page assembled: {product.name}")
        return page

    def build_faq_page(self, product: ProductData, questions: list[str]) -> FAQPage:
        log_agent_thought("BuilderAgent", "Assembling FAQ Page with accurate answers", {
            "product": product.name,
            "questions_to_answer": len(questions[:8])
        })
        
        # Build COMPLETE product context for accurate answers
        complete_product_data = f"""
=== COMPLETE PRODUCT DATA (USE ONLY THIS FOR ANSWERS) ===

PRODUCT NAME: {product.name}
CONCENTRATION: {product.concentration}
PRICE: ₹{product.price_inr}

SUITABLE SKIN TYPES: {', '.join(product.skin_type)}

KEY INGREDIENTS:
{chr(10).join(f'- {ing}' for ing in product.key_ingredients)}

BENEFITS:
{chr(10).join(f'- {ben}' for ben in product.benefits)}

USAGE INSTRUCTIONS: {product.usage_instructions}

SIDE EFFECTS & WARNINGS: {product.side_effects or 'None specified'}

=== END OF PRODUCT DATA ===
"""
        
        selected_qs = questions[:8]  # Use 8 questions for comprehensive FAQ
        
        builder_logger.debug(f"Generating accurate answers for {len(selected_qs)} questions...")
        
        prompt = f"""
You are a Product Information Specialist. Your job is to provide 100% ACCURATE answers.

{complete_product_data}

QUESTIONS TO ANSWER:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(selected_qs))}

STRICT RULES FOR ANSWERING:
1. ONLY use information from the PRODUCT DATA above - NO external knowledge
2. Be DEFINITIVE - Never say "not specified", "may", "might", "could", "it's recommended to consult"
3. If asked about usage, quote the exact instructions from the data
4. If asked about side effects, state them directly as facts
5. If asked about ingredients, list them exactly as provided
6. If asked about price/skin types, state the exact values
7. Categorize each FAQ appropriately: "Usage", "Safety", "Ingredients", "Product Info"
8. Keep answers concise but complete (2-3 sentences max)

ANSWER FORMAT EXAMPLES:
- Q: "How often should I use this?" → A: "Use only in your PM routine. Beginners should start 1-2 times a week, gradually increasing to every other night."
- Q: "What are the side effects?" → A: "Initial side effects include purging, redness, peeling, or dryness during the first 2-4 weeks. If severe burning occurs, wash off immediately."
- Q: "Is it safe during pregnancy?" → A: "No. This product is strictly not recommended for use during pregnancy or breastfeeding."

Return a list of FAQ Items with category, question, and accurate answer.
"""
        
        class FAQList(BaseModel):
            items: list[FAQItem]
            
        result = get_structured_data(prompt, FAQList)
        
        page = FAQPage(
            product_name=product.name,
            faqs=result.items
        )
        
        builder_logger.info(f"✓ FAQ page assembled: {len(result.items)} Q&As")
        for item in result.items[:3]:
            builder_logger.debug(f"  └─ [{item.category}] {item.question[:40]}...")
        
        return page

    def build_comparison_page(self, product: ProductData, competitor: CompetitorData) -> ComparisonPage:
        log_agent_thought("BuilderAgent", "Assembling Comparison Page", {
            "our_product": product.name,
            "competitor": competitor.name
        })
        
        # Run Comparison Block
        builder_logger.debug("Running ComparisonBlock...")
        table_data = compare_products_block(product, competitor)
        builder_logger.debug(f"  └─ Generated {len(table_data)} comparison rows")
        
        # Convert dicts to Pydantic models
        rows = [ComparisonRow(**row) for row in table_data]
        
        # Count wins
        our_wins = sum(1 for row in rows if "Us" in row.verdict)
        their_wins = sum(1 for row in rows if "Competitor" in row.verdict and "Us" not in row.verdict)
        
        builder_logger.debug(f"  └─ Verdicts: Our product wins {our_wins}, Competitor wins {their_wins}")
        
        # Generate accurate summary based on actual data
        our_advantages = []
        if product.concentration:
            our_advantages.append(f"clinically effective {product.concentration}")
        our_advantages.append(f"{len(product.key_ingredients)} premium active ingredients")
        
        summary = f"{product.name} offers superior value with {', '.join(our_advantages)}, compared to {competitor.name}'s basic formulation."
        
        page = ComparisonPage(
            title=f"{product.name} vs {competitor.name}",
            competitor_name=competitor.name,
            comparison_table=rows,
            summary_verdict=summary
        )
        
        builder_logger.info(f"✓ Comparison page assembled: {product.name} vs {competitor.name}")
        
        return page
