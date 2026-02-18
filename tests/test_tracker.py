import os
import json
from pathlib import Path
import notes_export_utils as utils


def test_uses_subdirs_true(monkeypatch, tmp_path):
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'true')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))
    assert tracker._uses_subdirs() is True


def test_uses_subdirs_false(monkeypatch, tmp_path):
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'false')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))
    assert tracker._uses_subdirs() is False


def test_get_output_path_with_subdirs(monkeypatch, tmp_path):
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'true')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))
    output = tracker.get_output_path('pdf', 'folder', 'note', '.pdf')
    expected = Path(tmp_path) / 'pdf' / 'folder' / 'note.pdf'
    assert output == expected
    assert output.parent.is_dir()


def test_get_output_path_without_subdirs(monkeypatch, tmp_path):
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'false')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))
    output = tracker.get_output_path('pdf', 'folder', 'note', '.pdf')
    expected = Path(tmp_path) / 'pdf' / 'note.pdf'
    assert output == expected
    assert output.parent.is_dir()


def test_get_output_path_nested_subfolder(monkeypatch, tmp_path):
    """Output path should mirror nested folder structure (e.g. iCloud-Latino/Esercizi)."""
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'true')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))
    output = tracker.get_output_path('pdf', 'iCloud-Latino/Esercizi', 'note', '.pdf')
    expected = Path(tmp_path) / 'pdf' / 'iCloud-Latino' / 'Esercizi' / 'note.pdf'
    assert output == expected
    assert output.parent.is_dir()


def test_get_all_data_files_finds_nested_json(monkeypatch, tmp_path):
    """get_all_data_files should return JSON files in subdirectories of data/."""
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'true')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))

    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    # Top-level JSON
    top_json = data_dir / 'iCloud-Latino.json'
    top_json.write_text('{}')

    # Nested JSON representing Latino/Esercizi
    nested_dir = data_dir / 'iCloud-Latino'
    nested_dir.mkdir()
    nested_json = nested_dir / 'Esercizi.json'
    nested_json.write_text('{}')

    found = tracker.get_all_data_files()
    found_paths = set(found)
    assert top_json in found_paths
    assert nested_json in found_paths


def test_get_notes_to_process_nested_folder(monkeypatch, tmp_path):
    """Notes in nested JSON data files should resolve to nested html source paths."""
    monkeypatch.setenv('NOTES_EXPORT_USE_SUBDIRS', 'true')
    tracker = utils.NotesExportTracker(root_directory=str(tmp_path))

    # Create data/iCloud-Latino/Esercizi.json
    data_dir = tmp_path / 'data'
    nested_data_dir = data_dir / 'iCloud-Latino'
    nested_data_dir.mkdir(parents=True)
    note_data = {
        'note-1': {
            'filename': 'my-note',
            'created': 'Thursday, August 26, 2021 at 7:38:15 PM',
            'modified': 'Thursday, August 26, 2021 at 7:38:15 PM',
            'lastExported': '2021-08-26',
        }
    }
    (nested_data_dir / 'Esercizi.json').write_text(json.dumps(note_data))

    # Create corresponding html source file at html/iCloud-Latino/Esercizi/my-note.html
    html_dir = tmp_path / 'html' / 'iCloud-Latino' / 'Esercizi'
    html_dir.mkdir(parents=True)
    (html_dir / 'my-note.html').write_text('<html><body>test</body></html>')

    notes = tracker.get_notes_to_process('markdown')
    assert len(notes) == 1
    note = notes[0]
    assert note['notebook'] == 'iCloud-Latino/Esercizi'
    assert note['source_file'] == html_dir / 'my-note.html'
