import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to make imports work when running tests directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# This allows running tests with 'pytest uhmactually/tests'
# No fixtures needed for now, but we can add them here as needed
