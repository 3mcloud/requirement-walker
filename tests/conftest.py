""" Fixtures, Fixtures, and Fixtures """

# Built In
from pathlib import Path

# 3rd Party
import pytest

# Owned

@pytest.fixture(scope='session')
def examples_path():
    """
    Return the absolute path to the examples.
    """
    cur_path = Path(__file__).parent.absolute()
    return cur_path / 'examples'
    