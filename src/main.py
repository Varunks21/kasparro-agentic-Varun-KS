import os
import json
from src.agents.parser_agent import parse_raw_data
from src.agents.strategy_agent import StrategyAgent
from src.agents.builder_agent import BuilderAgent
from src.utils.logger import (
    main_logger, 
    log_pipeline_start, 
    log_pipeline_complete, 
    log_file_saved,
    log_agent_thought
)


def save_json(filename: str, pydantic_obj):
    """Save a Pydantic object to JSON file."""
    path = os.path.join("output", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pydantic_obj.model_dump_json(indent=2))
    log_file_saved(path)


def main():
    # Initialize pipeline
    log_pipeline_start()
    
    # 1. PARSE
    log_agent_thought("Main", "Phase 1: Parsing raw product data")
    product_data = parse_raw_data("data/raw_input.txt")
    main_logger.debug(f"Parsed product: {product_data.name}")
    
    # 2. STRATEGIZE
    log_agent_thought("Main", "Phase 2: Strategy generation (competitor + FAQs)")
    strategist = StrategyAgent()
    competitor_data = strategist.generate_competitor(product_data)
    main_logger.debug(f"Generated competitor: {competitor_data.name}")
    
    questions = strategist.generate_faqs_concepts(product_data)
    main_logger.debug(f"Generated {len(questions)} FAQ questions")
    
    # 3. BUILD & ASSEMBLE
    log_agent_thought("Main", "Phase 3: Building content pages")
    builder = BuilderAgent()
    
    # Generate Product Page
    prod_page = builder.build_product_page(product_data)
    save_json("product_page.json", prod_page)
    
    # Generate FAQ Page
    faq_page = builder.build_faq_page(product_data, questions)
    save_json("faq.json", faq_page)
    
    # Generate Comparison Page
    comp_page = builder.build_comparison_page(product_data, competitor_data)
    save_json("comparison_page.json", comp_page)
    
    # Complete
    log_pipeline_complete()


if __name__ == "__main__":
    main()
