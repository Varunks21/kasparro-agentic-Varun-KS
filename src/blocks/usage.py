from src.utils.llm_client import get_text_content

def extract_usage_block(raw_usage_text: str) -> list[str]:
    """
    Logic Block: Converts paragraph usage text into clear numbered steps.
    """
    prompt = f"""
    You are a Technical Writer.
    
    Task: Convert the following usage instructions into a clear, step-by-step list.
    
    Input Text: "{raw_usage_text}"
    
    Rules:
    - Break it down into logical steps (e.g., 1. Cleanse, 2. Apply...).
    - Keep each step under 10 words.
    - Return ONLY the steps, one per line.
    """
    
    raw_text = get_text_content(prompt)
    
    # Clean up output
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    return lines