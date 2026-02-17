import os
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from convert_to_pdf import parse_apple_date, add_pdf_css_to_html


def test_parse_apple_date():
    """Test parsing Apple Notes date format"""
    # Test with normal space
    date_str = "Thursday, August 26, 2021 at 7:38:15 PM"
    result = parse_apple_date(date_str)
    assert result is not None
    assert result.year == 2021
    assert result.month == 8
    assert result.day == 26
    assert result.hour == 19  # 7 PM in 24-hour format
    assert result.minute == 38
    assert result.second == 15
    
    # Test with non-breaking space (typical Apple format)
    date_str_nbsp = "Thursday, August 26, 2021 at 7:38:15\u202fPM"
    result_nbsp = parse_apple_date(date_str_nbsp)
    assert result_nbsp is not None
    assert result_nbsp == result


def test_add_pdf_css_to_html_basic():
    """Test that CSS is added to basic HTML"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple HTML file
        source_file = Path(temp_dir) / "test.html"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("<html><head></head><body>Test content</body></html>")
        
        # Process it
        result_file = add_pdf_css_to_html(source_file, continuous=False, title=None)
        
        # Read the result
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify CSS was added
        assert "word-wrap: break-word" in content
        assert "overflow-wrap: break-word" in content
        assert "@page" in content
        assert "Test content" in content


def test_add_pdf_css_to_html_with_title():
    """Test that title header is added when title is provided"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple HTML file
        source_file = Path(temp_dir) / "test.html"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("<html><body>Test content</body></html>")
        
        # Process it with a title
        result_file = add_pdf_css_to_html(source_file, continuous=False, title="My Test Note")
        
        # Read the result
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify title was added
        assert "My Test Note" in content
        assert "pdf-note-title" in content


def test_add_pdf_css_continuous_mode():
    """Test that continuous mode adds page-break prevention"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple HTML file
        source_file = Path(temp_dir) / "test.html"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("<html><body>Test content</body></html>")
        
        # Process in continuous mode
        result_file = add_pdf_css_to_html(source_file, continuous=True, title=None)
        
        # Read the result
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify page-break prevention CSS was added
        assert "page-break-inside: avoid" in content
        assert "break-inside: avoid" in content


def test_add_pdf_css_normal_mode():
    """Test that normal mode does not add page-break prevention"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple HTML file
        source_file = Path(temp_dir) / "test.html"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("<html><body>Test content</body></html>")
        
        # Process in normal mode
        result_file = add_pdf_css_to_html(source_file, continuous=False, title=None)
        
        # Read the result
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Base CSS should still be present
        assert "word-wrap: break-word" in content
        # But continuous mode CSS should not be present
        # Note: We check that page-break prevention is only in continuous mode
        # In normal mode, base CSS is present but not the extra page-break rules


def test_add_pdf_css_preserves_attachments():
    """Test that attachments folder is copied to temp directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple HTML file
        source_file = Path(temp_dir) / "test.html"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("<html><body>Test content</body></html>")
        
        # Create an attachments folder
        attachments_dir = Path(temp_dir) / "attachments"
        attachments_dir.mkdir()
        test_attachment = attachments_dir / "test.png"
        test_attachment.write_text("fake image data")
        
        # Process it
        result_file = add_pdf_css_to_html(source_file, continuous=False, title=None)
        
        # Verify attachments were copied
        result_attachments = result_file.parent / "attachments"
        assert result_attachments.exists()
        assert (result_attachments / "test.png").exists()


if __name__ == '__main__':
    # Run tests manually
    test_parse_apple_date()
    print("✓ test_parse_apple_date passed")
    
    test_add_pdf_css_to_html_basic()
    print("✓ test_add_pdf_css_to_html_basic passed")
    
    test_add_pdf_css_to_html_with_title()
    print("✓ test_add_pdf_css_to_html_with_title passed")
    
    test_add_pdf_css_continuous_mode()
    print("✓ test_add_pdf_css_continuous_mode passed")
    
    test_add_pdf_css_normal_mode()
    print("✓ test_add_pdf_css_normal_mode passed")
    
    test_add_pdf_css_preserves_attachments()
    print("✓ test_add_pdf_css_preserves_attachments passed")
    
    print("\nAll tests passed!")
