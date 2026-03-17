# tests/conftest.py

import sys
from pathlib import Path

# force pytest to use the local repo version of arvis
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))