from src.models.internal import ProductData, CompetitorData
from src.models.output import ProductPage, FAQPage, ComparisonPage, ComparisonRow, FAQItem

class TemplateEngine:
    """
    The 'Template Engine of Your Own Design'. 
    It is responsible for strictly mapping data + logic blocks into the final JSON structure.
    """

    @staticmethod
    def render_product_page(product: ProductData, benefits_copy: list[str], usage_steps: list[str]) -> ProductPage:
        """
        Assembles the Product Page JSON.
        """
        return ProductPage(
            title=product.name,
            price=f"₹{product.price_inr}",
            description=f"A premium {product.concentration or ''} serum designed for {' & '.join(product.skin_type)} skin.",
            key_benefits=benefits_copy,
            usage_guide=usage_steps,
            ingredients_list=product.key_ingredients
        )

    @staticmethod
    def render_faq_page(product_name: str, qa_pairs: list[dict]) -> FAQPage:
        """
        Assembles the FAQ Page JSON.
        """
        # Convert dict items to proper FAQItem models
        items = [FAQItem(**item) for item in qa_pairs]
        
        return FAQPage(
            product_name=product_name,
            faqs=items
        )

    @staticmethod
    def render_comparison_page(product_name: str, competitor_name: str, comparison_data: list[dict]) -> ComparisonPage:
        """
        Assembles the Comparison Page JSON.
        """
        rows = [ComparisonRow(**row) for row in comparison_data]
        
        return ComparisonPage(
            title=f"{product_name} vs {competitor_name}",
            competitor_name=competitor_name,
            comparison_table=rows,
            summary_verdict=f"{product_name} is the superior choice for targeted results."
        )