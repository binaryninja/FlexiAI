#!/usr/bin/env python3
"""
Entry point for running FlexiAI as a module with python -m flexiai
"""

import sys
from .main import main

if __name__ == "__main__":
    sys.exit(main())
