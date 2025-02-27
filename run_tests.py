#!/usr/bin/env python3
import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Discover and run all tests
if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())
