# tests/test_integrity.py
import json
import os
import pytest
from src.models.output import ProductPage, FAQPage, ComparisonPage

def test_output_files_exist():
    """Ensure all 3 required files were generated."""
    assert os.path.exists("output/product_page.json")
    assert os.path.exists("output/faq.json")
    assert os.path.exists("output/comparison_page.json")

def test_product_page_schema():
    """Validate that the generated Product Page matches the strict Schema."""
    with open("output/product_page.json", "r") as f:
        data = json.load(f)
    # This will raise an error if the data is wrong
    assert ProductPage(**data)

def test_faq_page_logic():
    """Ensure we have at least 5 FAQs as required."""
    with open("output/faq.json", "r") as f:
        data = json.load(f)
    page = FAQPage(**data)
    assert len(page.faqs) >= 5
    assert page.product_name != ""

def test_comparison_winner():
    """Check that we actually declared a winner."""
    with open("output/comparison_page.json", "r") as f:
        data = json.load(f)
    page = ComparisonPage(**data)
    assert len(page.comparison_table) > 0
    # Ideally, our product should win most categories!
    assert "Winner" in page.comparison_table[0].verdict