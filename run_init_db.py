"""
Convenience script to run database initialization from project root
"""

import sys
import os

# Add app/database to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'database'))

# Import and run initialization
from init_db import main

if __name__ == '__main__':
    main()
