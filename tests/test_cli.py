import pytest
from logic import main, generate_message

# --- Unit Tests ---
def test_generate_message_default():
    assert generate_message("Claire") == "Hello, Claire!"

def test_generate_message_formal():
    assert generate_message("Samson", formal=True) == "Greetings, Samson!"

# --- Functional/CLI Tests ---
def test_cli_no_args(capsys):
    # Simulate running agape with no arguments
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "Hello, World!"

def test_cli_with_name(capsys):
    # Simulate running agape with a name argument
    exit_code = main(["Alice"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "Hello, Alice!"

def test_cli_formal_greeting(capsys):
    # Simulate running agape with a name and --formal flag
    exit_code = main(["Bob", "--formal"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "Greetings, Bob!"