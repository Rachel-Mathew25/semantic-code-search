import sys
from pathlib import Path

# Add the project root to sys.path so pytest can resolve 'src.*' imports
# the same way running 'python -m ...' from the project root would.
sys.path.insert(0, str(Path(__file__).parent))
