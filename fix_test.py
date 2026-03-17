import re
with open("samples/snippets/encryption_test.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.startswith("def test_") or line.startswith("@pytest.fixture"):
        # Make sure there are two blank lines before it
        # by checking the end of new_lines
        if not (len(new_lines) >= 2 and new_lines[-1] == "\n" and new_lines[-2] == "\n"):
            while len(new_lines) > 0 and new_lines[-1] == "\n":
                new_lines.pop()
            if len(new_lines) > 0:
                new_lines.append("\n")
                new_lines.append("\n")
    if line.startswith("def test_blob"):
        # make sure no blank lines between @pytest.fixture and def test_blob
        while len(new_lines) > 0 and new_lines[-1] == "\n":
            new_lines.pop()
    new_lines.append(line)

with open("samples/snippets/encryption_test.py", "w") as f:
    f.writelines(new_lines)
