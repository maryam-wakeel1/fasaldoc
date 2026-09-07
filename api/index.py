import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.main import app