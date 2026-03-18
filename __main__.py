"""Entry point for running validator_oop as a module.

This allows the package to be executed with: python -m validator_oop
"""

from validator_oop.main import main
import sys

if __name__ == "__main__":
    sys.exit(main())

