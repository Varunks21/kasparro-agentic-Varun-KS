from src.utils.llm_client import get_text_content

def generate_benefits_block(ingredients: list[str], claimed_benefits: list[str]) -> list[str]:
    """
    Logic Block: Takes ingredients and claims, returns accurate marketing bullet points.
    """
    prompt = f"""
You are a Skincare Product Copywriter. Write accurate marketing copy based ONLY on the provided data.

INGREDIENTS PROVIDED:
{chr(10).join(f'- {ing}' for ing in ingredients)}

CLAIMED BENEFITS PROVIDED:
{chr(10).join(f'- {ben}' for ben in claimed_benefits)}

TASK: Write exactly 4 marketing bullet points that:
1. Directly connect specific ingredients to their benefits
2. Use ONLY the benefits listed above - do not invent new claims
3. Be factual and professional - no exaggeration
4. Each bullet should be 1 sentence (15-20 words max)

FORMAT: Return ONLY 4 bullet points, one per line, starting with the ingredient name.

Example format:
- [Ingredient] delivers [specific benefit from the list]
"""
    
    raw_text = get_text_content(prompt)
    
    # Clean up the output into a python list
    lines = [line.strip().lstrip('- ').lstrip('* ').strip() for line in raw_text.split('\n') if line.strip()]
    # Filter to only lines that look like actual content
    lines = [line for line in lines if len(line) > 10 and not line.startswith('#')]
    return lines[:4]  # Return exactly 4 benefits
