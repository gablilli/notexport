import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from convert_to_pdf import parse_apple_date, add_pdf_css_to_html
import unittest.mock as mock


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
    """Test that normal mode includes base CSS but not the continuous page-break-prevention wildcard"""
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
        
        # Base CSS should be present
        assert "word-wrap: break-word" in content
        
        # Image sizing CSS should always be present
        assert "max-height: 277mm" in content


def test_add_pdf_css_images_fit_in_page():
    """Test that image CSS constrains images to fit within a page"""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = Path(temp_dir) / "test.html"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write("<html><body><img src='test.png'></body></html>")
        
        result_file = add_pdf_css_to_html(source_file, continuous=False, title=None)
        
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Images must be constrained to page height
        assert "max-height: 277mm" in content
        # Images must not be cut across pages
        assert "page-break-inside: avoid" in content
        assert "break-inside: avoid" in content
        # Each image must force a page break after it
        assert "page-break-after: always" in content
        assert "break-after: always" in content


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


# ---------------------------------------------------------------------------
# Tests for weasyprint availability detection and error messages
# ---------------------------------------------------------------------------

import convert_to_pdf as _pdf_module


def _run_convert_with_mocked_weasyprint(available, import_error, tmp_path, monkeypatch, capsys):
    """Helper: patch module globals and run convert_html_to_pdf with a fake tracker."""
    import convert_to_pdf

    # Build a minimal tracker mock
    tracker = mock.MagicMock()
    tracker.root_directory = str(tmp_path)
    # Return one fake note so the "no notes" early-return is not triggered
    tracker.get_notes_to_process.return_value = [
        {
            'note_id': '1',
            'notebook': 'TestBook',
            'filename': 'TestNote',
            'source_file': tmp_path / 'TestNote.html',
            'json_file': tmp_path / 'TestBook.json',
            'note_info': {},
        }
    ]

    monkeypatch.setattr(convert_to_pdf, '_WEASYPRINT_AVAILABLE', available)
    monkeypatch.setattr(convert_to_pdf, '_WEASYPRINT_IMPORT_ERROR', import_error)

    with mock.patch('convert_to_pdf.get_tracker', return_value=tracker):
        with pytest.raises(SystemExit) as exc_info:
            convert_to_pdf.convert_html_to_pdf()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    return captured.err


def test_weasyprint_not_installed_error_message(tmp_path, monkeypatch, capsys):
    """When weasyprint is not installed, the error message says 'not installed'."""
    err = _run_convert_with_mocked_weasyprint(
        available=False,
        import_error=("not_installed", None),
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert "not installed" in err
    assert "pip install" in err
    assert "system libraries" not in err


def test_weasyprint_system_libs_error_message(tmp_path, monkeypatch, capsys):
    """When weasyprint is installed but system libraries are missing, error says so."""
    err = _run_convert_with_mocked_weasyprint(
        available=False,
        import_error=("system_libs", OSError("libpango-1.0.so.0: cannot open shared object file")),
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert "system libraries" in err
    assert "doc.courtbouillon.org" in err
    # Should NOT say "not installed" (weasyprint itself IS installed)
    assert "not installed" not in err


def test_weasyprint_unknown_error_message(tmp_path, monkeypatch, capsys):
    """When weasyprint fails with an unknown error, details are shown."""
    err = _run_convert_with_mocked_weasyprint(
        available=False,
        import_error=("unknown", AttributeError("some internal error")),
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        capsys=capsys,
    )
    assert "failed to load" in err
    assert "AttributeError" in err
