from functools import wraps
from typing import Union
import inspect

# Registry of all validators
VALIDATORS = {}
