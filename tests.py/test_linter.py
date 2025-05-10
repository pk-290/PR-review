from app.linter import run_linters

def test_run_linters_basic():
    hunk = "+print('debugging')\n+some_long_line = 'x' * 101\n+try:\n+    pass\n+except:\n+    pass"
    result = run_linters("dummy.py", hunk)
    assert isinstance(result, list)
    assert any("debug" in r["type"] for r in result)
    assert any("style" in r["type"] for r in result)
    assert any("bug" in r["type"] for r in result)


