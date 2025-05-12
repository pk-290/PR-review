from langchain.tools import BaseTool
import tempfile
import os
import subprocess
import ast
from radon.complexity import cc_visit
from logging_wrapper import log_async_exceptions,log_exceptions
import textwrap

@log_exceptions
def run_static_analyzer(code_hunk: str) -> str:
        """
        Analyze the provided Python code hunk and report detected code smells.
        """
        code_hunk = textwrap.dedent(code_hunk)
        results = []

        # 1. Check cyclomatic complexity using radon
        try:
            blocks = cc_visit(code_hunk)
            for block in blocks:
                if block.complexity > 10:
                    results.append(
                        f"Function '{block.name}' has high cyclomatic complexity: {block.complexity}."
                    )
        except Exception as e:
            results.append(f"Cyclomatic complexity analysis error: {e}")

        # 2. Detect deeply nested conditionals
        try:
            tree = ast.parse(code_hunk)
            max_depth = 0

            def depth(node, current):
                nonlocal max_depth
                if isinstance(node, (ast.If, ast.For, ast.While)):
                    current += 1
                    max_depth = max(max_depth, current)
                for child in ast.iter_child_nodes(node):
                    depth(child, current)

            depth(tree, 0)
            if max_depth > 3:
                results.append(f"Deeply nested control flow detected (depth={max_depth}).")
        except Exception as e:
            results.append(f"AST analysis error: {e}")

        # 3. Check for long functions (over 50 lines)
        lines = code_hunk.splitlines()
        func_line_counts = {}
        current_name = None
        current_count = 0
        for line in lines:
            if line.strip().startswith('def '):
                if current_name and current_count > 50:
                    results.append(
                        f"Function '{current_name}' is too long ({current_count} lines)."
                    )
                current_name = line.strip().split()[1].split('(')[0]
                current_count = 1
            elif current_name:
                current_count += 1
        if current_name and current_count > 50:
            results.append(
                f"Function '{current_name}' is too long ({current_count} lines)."
            )

        # 4. Invoke pylint for naming and style issues
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(code_hunk)
                tmp_path = tmp.name
            result = subprocess.run([
                'pylint', tmp_path, '--disable=all', '--enable=C0103,C0301,E1101'
            ], capture_output=True, text=True)
            if result.stdout:
                results.append("Pylint issues:\n" + result.stdout)
        except Exception as e:
            results.append(f"Pylint analysis error: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

        if not results:
            return "No obvious code smells detected."
        return "\n".join(results)

