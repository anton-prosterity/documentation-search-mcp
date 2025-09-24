import os
import sys

# Ensure example test projects can import their local modules when pytest is run
# from the repository root.
EXAMPLE_ROOTS = ["pytest-test-project"]

for folder in EXAMPLE_ROOTS:
    path = os.path.join(os.path.dirname(__file__), folder)
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
