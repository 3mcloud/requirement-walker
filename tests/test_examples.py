""" Simple testing based on the example in the README """

# 3rd Party
from requirement_walker import walk, LocalRequirement, FailedRequirement

# Owned

def test_simple_assertions():
    """ Use the walker and make some simple assertions. """
    entries = list(walk('./examples/example_application/project_requirements.txt'))
    assert len(entries) == 16
    assert not any(isinstance(entry.requirement, FailedRequirement) for entry in entries)
    local_reqs = [entry.requirement for entry in entries if isinstance(entry.requirement, LocalRequirement)]
    assert len(local_reqs) == 3

def test_simple_req_file():
    """ Test the sole requirements.txt file """
    entries = list(walk('./examples/requirements.txt'))
    assert len(entries) == 11
    failed_reqs = [entry.requirement for entry in entries if isinstance(entry.requirement, FailedRequirement)]
    local_reqs = [entry.requirement for entry in entries if isinstance(entry.requirement, LocalRequirement)]
    assert len(local_reqs) == 1
    assert len(failed_reqs) == 1
