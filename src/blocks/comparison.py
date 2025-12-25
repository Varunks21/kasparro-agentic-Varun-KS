from src.models.internal import ProductData, CompetitorData

def compare_products_block(product: ProductData, competitor: CompetitorData) -> list[dict]:
    """
    Logic Block: Generates a structured comparison table between our product and the competitor.
    Returns a list of dicts with feature comparisons.
    """
    comparison_rows = []
    
    # 1. Price Comparison
    our_price = product.price_inr
    their_price = competitor.price_inr
    price_verdict = "Winner: Us" if our_price <= their_price else "Winner: Competitor"
    if our_price < their_price:
        price_verdict = "Winner: Us (Better Value)"
    elif our_price == their_price:
        price_verdict = "Tie"
    
    comparison_rows.append({
        "feature": "Price",
        "our_product": f"₹{our_price}",
        "competitor_product": f"₹{their_price}",
        "verdict": price_verdict
    })
    
    # 2. Ingredients Count
    our_ingredients = len(product.key_ingredients)
    their_ingredients = len(competitor.key_ingredients)
    
    comparison_rows.append({
        "feature": "Active Ingredients",
        "our_product": f"{our_ingredients} key ingredients",
        "competitor_product": f"{their_ingredients} key ingredients",
        "verdict": "Winner: Us" if our_ingredients >= their_ingredients else "Winner: Competitor"
    })
    
    # 3. Ingredient Quality (based on name matching common premium ingredients)
    premium_ingredients = ["vitamin c", "l-ascorbic", "hyaluronic", "retinol", "niacinamide", "ferulic"]
    our_premium = sum(1 for ing in product.key_ingredients if any(p in ing.lower() for p in premium_ingredients))
    their_premium = sum(1 for ing in competitor.key_ingredients if any(p in ing.lower() for p in premium_ingredients))
    
    comparison_rows.append({
        "feature": "Premium Ingredients",
        "our_product": f"{our_premium} premium actives",
        "competitor_product": f"{their_premium} premium actives", 
        "verdict": "Winner: Us" if our_premium >= their_premium else "Winner: Competitor"
    })
    
    # 4. Concentration (if available)
    if product.concentration:
        comparison_rows.append({
            "feature": "Active Concentration",
            "our_product": product.concentration,
            "competitor_product": "Not specified",
            "verdict": "Winner: Us (Transparency)"
        })
    
    # 5. Pros comparison
    comparison_rows.append({
        "feature": "Key Strengths",
        "our_product": ", ".join(product.benefits[:2]) if product.benefits else "Multiple benefits",
        "competitor_product": ", ".join(competitor.pros) if competitor.pros else "Basic formulation",
        "verdict": "Winner: Us"
    })
    
    # 6. Known Issues
    comparison_rows.append({
        "feature": "Drawbacks",
        "our_product": product.side_effects or "Minimal side effects",
        "competitor_product": ", ".join(competitor.cons) if competitor.cons else "Unknown",
        "verdict": "Winner: Us" if competitor.cons else "Tie"
    })
    
    return comparison_rows

