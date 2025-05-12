import subprocess
import ast
import pytest

# Assume run_static_analyzer is defined in static_analyzer.py
from app.static_analyzer_tools import run_static_analyzer

class DummyBlock:
    def __init__(self, name, complexity):
        self.name = name
        self.complexity = complexity

class DummyResult:
    def __init__(self, stdout):
        self.stdout = stdout


def test_no_smells(monkeypatch):
    # Simple function should yield no smells
    code = """
    def foo():
        return 42
    """

    # Monkeypatch radon.cc_visit to return low complexity
    import radon.complexity as rc
    monkeypatch.setattr(rc, 'cc_visit', lambda x: [DummyBlock('foo', 1)])
    # Monkeypatch subprocess.run to return no pylint issues
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: DummyResult(stdout=""))

    result = run_static_analyzer(code)
    assert result.strip() == "No obvious code smells detected."


def test_high_cyclomatic():
    # This function has 12 decision points → complexity = 12 (>10 threshold)
    code = """def complex_function(x):
        if x == 1:
            pass
        elif x == 2:
            pass
        elif x == 3:
            pass
        elif x == 4:
            pass
        elif x == 5:
            pass
        elif x == 6:
            pass
        elif x == 7:
            pass
        elif x == 8:
            pass
        elif x == 9:
            pass
        elif x == 10:
            pass
        elif x == 11:
            pass
        else:
            pass
    """
    result = run_static_analyzer(code)
    # It should mention “high cyclomatic complexity”
    assert "high cyclomatic complexity" in result, f"Expected cyclomatic warning but got:\n{result}"


def test_deeply_nested():
    # Create code with 4 nested ifs
    code = """
    def nested():
        if True:
            if True:
                if True:
                    if True:
                        pass
    """
    # Let cc_visit return no complexity issues
    import radon.complexity as rc
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(rc, 'cc_visit', lambda x: [])
    # Stub subprocess
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: DummyResult(stdout=""))

    result = run_static_analyzer(code)
    assert "Deeply nested control flow" in result
    monkeypatch.undo()


def test_long_function(monkeypatch):
    # Generate function longer than 50 lines
    lines = ['def long_fn():'] + ['    x = %d' % i for i in range(60)]
    code = "\n".join(lines)
    import radon.complexity as rc
    monkeypatch.setattr(rc, 'cc_visit', lambda x: [])
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: DummyResult(stdout=""))

    result = run_static_analyzer(code)
    assert "too long" in result
    assert "long_fn" in result


def test_pylint_issues(monkeypatch):
    # Code that triggers a pylint naming issue
    code = """
    def BadName():
        return
    """
    import radon.complexity as rc
    monkeypatch.setattr(rc, 'cc_visit', lambda x: [])
    # Simulate pylint output
    fake_output = "C0103: Invalid function name 'BadName'"
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: DummyResult(stdout=fake_output))

    result = run_static_analyzer(code)
    assert "Pylint issues" in result
    assert "C0103" in result
