import os
from src.models.internal import ProductData
from src.utils.llm_client import get_structured_data
from src.utils.logger import parser_logger, log_agent_thought


def parse_raw_data(file_path: str) -> ProductData:
    """
    Reads the raw text file and uses Gemini to parse it into a structured ProductData object.
    """
    
    # 1. Read the file content
    if not os.path.exists(file_path):
        parser_logger.error(f"Input file not found: {file_path}")
        raise FileNotFoundError(f"Input file not found at: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    log_agent_thought("ParserAgent", f"Reading data from {file_path}", {
        "file_size": f"{len(raw_text)} characters",
        "lines": len(raw_text.split('\n'))
    })

    # 2. Construct the prompt
    prompt = f"""
    You are an expert Data Parsing Agent.
    Your job is to extract product details from the raw text provided below.
    
    Rules:
    - Extract exact values where possible.
    - If a value is missing, use reasonable context or leave as null (do not hallucinate).
    - Convert price to a float number (remove currency symbols).
    - 'skin_type' should be a list of strings.
    - 'usage_instructions' should capture the full 'How to Use' text.
    
    Raw Text:
    {raw_text}
    """

    # 3. Call Gemini via our client
    try:
        log_agent_thought("ParserAgent", "Sending data to LLM for structured extraction")
        product_data = get_structured_data(prompt, ProductData)
        
        parser_logger.info(f"✓ Data parsed successfully: {product_data.name}")
        parser_logger.debug(f"  └─ Price: ₹{product_data.price_inr}")
        parser_logger.debug(f"  └─ Ingredients: {len(product_data.key_ingredients)} items")
        parser_logger.debug(f"  └─ Benefits: {len(product_data.benefits)} items")
        
        return product_data
        
    except Exception as e:
        parser_logger.error(f"Failed to parse data: {e}")
        raise e


if __name__ == "__main__":
    # Test the agent directly
    data = parse_raw_data("data/raw_input.txt")
    parser_logger.info(data.model_dump_json(indent=2))
