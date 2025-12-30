import pytest
import os
import json
from src.logic import main, DB_FILE

@pytest.fixture
def temp_db_file(tmp_path, monkeypatch):
    """Creates a temporary tasks.json for each test."""
    temp_file = tmp_path / "test_tasks.json"
    monkeypatch.setattr("src.logic.DB_FILE", str(temp_file))
    return temp_file

def test_add_task(temp_db_file, capsys):
    main(["add", "Dummy Task"])
    out = capsys.readouterr().out
    assert "Task added: Dummy Task" in out

    with open(temp_db_file, "r") as file:
        data = json.load(file)
        assert len(data) == 1
        assert data[0]["description"] == "Dummy Task"

def test_list_all_tasks(temp_db_file, capsys):
    main(["add", "Task 1"])
    main(["add", "Task 2"])
    main(["list"])
    out = capsys.readouterr().out
    assert "1. [] Task 1" in out
    assert "2. [] Task 2" in out

def test_list_filtered_tasks(temp_db_file, capsys):
    main(["add", "Done Task"])
    main(["mark", "1", "--d"])
    main(["add", "Todo Task"])

    capsys.readouterr()  # Clear output

    main(["list", "--d"])
    out=capsys.readouterr().out

    assert "Done Task" in out
    assert "Todo Task" not in out

def test_update_task(temp_db_file, capsys):
    main(["add", "Old Title"])
    main(["update", "1", "New Title"])
    out = capsys.readouterr().out
    assert "Task #1 updated to: New Title" in out

    with open(temp_db_file, "r") as file:
        data = json.load(file)
        assert data[0]["description"] == "New Title"

def test_mark_progress(temp_db_file, capsys):
    main(["add", "Starting"])
    main(["mark", "1", "-p"])
    out = capsys.readouterr().out
    assert "marked as in-progress" in out
    
    main(["list"])
    out = capsys.readouterr().out
    assert "[○]" in out # Your logic uses ○ for progress

def test_delete_and_reindex(temp_db_file, capsys):
    main(["add", "Task A"])
    main(["add", "Task B"])
    main(["add", "Task C"])
    main(["delete", "2"])

    capsys.readouterr()  # Clear output
    
    main(["list"])
    out = capsys.readouterr().out

    assert "1. [] Task A" in out
    assert "2. [] Task C" in out
    assert "Task B" not in out

def test_invalid_id_error(temp_db_file, capsys):
    main(["delete", "99"])
    out = capsys.readouterr().out
    assert "Error: Task with ID 99 not found" in out