import typing
from src.models.internal import ProductData, CompetitorData
from src.utils.llm_client import get_structured_data
from src.utils.logger import strategy_logger, log_agent_thought
from pydantic import BaseModel


# We define a small temporary model just for the list of questions
class QuestionList(BaseModel):
    questions: typing.List[str]


class StrategyAgent:
    def __init__(self):
        strategy_logger.debug("StrategyAgent initialized")

    def generate_competitor(self, product: ProductData) -> CompetitorData:
        """
        Creates a fictional competitor that is similar but slightly inferior
        to our product to make for a good comparison.
        """
        log_agent_thought("StrategyAgent", "Designing fictional competitor", {
            "base_product": product.name,
            "price_point": f"₹{product.price_inr}",
            "target_competitor_price": f"₹{int(product.price_inr * 0.80)}"
        })
        
        prompt = f"""
        You are a Strategic Competitor Analysis Agent.
        
        Task: Create a FICTIONAL competitor product ("Product B") to compare against our product.
        
        Our Product Details:
        - Name: {product.name}
        - Price: ₹{product.price_inr}
        - Concentration: {product.concentration}
        - Ingredients: {', '.join(product.key_ingredients)}
        - Benefits: {', '.join(product.benefits)}
        
        STRICT Rules for Competitor:
        1. Name: Invent a realistic sounding skincare brand name (NOT a real brand).
        2. Price: Make it 15-25% cheaper than our product (₹{int(product.price_inr * 0.75)} to ₹{int(product.price_inr * 0.85)}).
        3. Ingredients: Use 3-4 common but LESS effective alternatives:
           - Lower concentration of active ingredients
           - No stabilizing ingredients
           - Missing key synergistic compounds
        4. Pros: List exactly 2 genuine-sounding pros (e.g., "Affordable", "Gentle formula")
        5. Cons: List exactly 2 specific cons that highlight our product's advantages (e.g., "Lower active concentration", "Missing key antioxidants")
        
        Return the result strictly as the CompetitorData JSON structure.
        """
        
        result = get_structured_data(prompt, CompetitorData)
        
        strategy_logger.info(f"✓ Competitor generated: {result.name}")
        strategy_logger.debug(f"  └─ Price: ₹{result.price_inr}")
        strategy_logger.debug(f"  └─ Pros: {result.pros}")
        strategy_logger.debug(f"  └─ Cons: {result.cons}")
        
        return result

    def generate_faqs_concepts(self, product: ProductData) -> typing.List[str]:
        """
        Generates questions that CAN be accurately answered from the product data.
        """
        log_agent_thought("StrategyAgent", "Generating answerable FAQ questions", {
            "product": product.name,
            "data_points_available": f"{len(product.key_ingredients)} ingredients, {len(product.benefits)} benefits"
        })
        
        # Build comprehensive product context
        product_context = f"""
        Product Name: {product.name}
        Concentration: {product.concentration}
        Price: ₹{product.price_inr}
        Suitable Skin Types: {', '.join(product.skin_type)}
        
        Key Ingredients: {', '.join(product.key_ingredients)}
        
        Benefits: {', '.join(product.benefits)}
        
        Usage Instructions: {product.usage_instructions}
        
        Side Effects/Warnings: {product.side_effects or 'None specified'}
        """
        
        prompt = f"""
        You are a Customer Experience Strategist creating an FAQ section.
        
        IMPORTANT: Generate questions that CAN BE 100% ACCURATELY ANSWERED using ONLY the product data below.
        Do NOT generate questions about information not present in the data.
        
        PRODUCT DATA:
        {product_context}
        
        Generate exactly 10 distinct questions across these categories:
        
        1. USAGE QUESTIONS (3 questions) - About how to use the product
           Examples: "How much should I apply?", "When should I use it?", "How often should beginners use it?"
        
        2. INGREDIENT QUESTIONS (2 questions) - About what's in the product
           Examples: "What is the active ingredient concentration?", "What are the key ingredients?"
        
        3. SAFETY QUESTIONS (3 questions) - About warnings and side effects
           Examples: "What side effects might occur?", "Is it safe during pregnancy?", "Do I need sunscreen?"
        
        4. PRODUCT INFO QUESTIONS (2 questions) - About price, skin types, storage
           Examples: "What skin types is this for?", "What is the price?", "How should I store it?"
        
        CRITICAL: Every question MUST be answerable from the product data provided above.
        
        Output: A list of exactly 10 question strings.
        """
        
        result = get_structured_data(prompt, QuestionList)
        
        strategy_logger.info(f"✓ Generated {len(result.questions)} FAQ questions")
        for i, q in enumerate(result.questions[:3], 1):
            strategy_logger.debug(f"  └─ Q{i}: {q[:50]}...")
        
        return result.questions


if __name__ == "__main__":
    from src.agents.parser_agent import parse_raw_data
    
    product = parse_raw_data("data/raw_input.txt")
    
    agent = StrategyAgent()
    comp = agent.generate_competitor(product)
    qs = agent.generate_faqs_concepts(product)
    
    strategy_logger.info("\n--- Fictional Competitor ---")
    strategy_logger.info(comp.model_dump_json(indent=2))
    
    strategy_logger.info("\n--- Brainstormed Questions ---")
    for q in qs:
        strategy_logger.info(f"- {q}")
