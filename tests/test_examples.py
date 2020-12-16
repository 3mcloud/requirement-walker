""" Simple testing based on the example in the README """

# Built In
from pathlib import Path

# 3rd Party
from requirement_walker import LocalRequirement, FailedRequirement, RequirementFile

# Owned

def test_simple_assertions(examples_path):
    """ Use the walker and make some simple assertions. """
    entries = list(RequirementFile(examples_path / './example_application/project_requirements.txt'))
    assert len(entries) == 8
    git_url_types = []
    for e in entries:
        is_git_url, protocol = e.is_git(return_protocol=True)
        if is_git_url:
            git_url_types.append(protocol)
    assert len(git_url_types) == 3
    assert set(git_url_types) == {'ssh', 'https', 'http'}

def test_simple_req_file(examples_path):
    """ Test the sole requirements.txt file """
    entries = list(RequirementFile(examples_path / './requirements.txt'))
    assert len(entries) == 11

def test_recursive_iter(examples_path):
    """ Use the walker and make some simple assertions. """
    r_file = RequirementFile(examples_path / './example_application/project_requirements.txt')
    all_entries = list(r_file.iter_recursive())
    assert len(all_entries) == 26 # Including empty lines and comments
    reqs_only = [entry for entry in all_entries if entry.requirement]
    assert len(reqs_only) == 18 # Not including empty lines, comments only, and req files.

def test_output_file(examples_path):
    """ Try outputting requirements to a single  file """
    r_file = RequirementFile(examples_path / './example_application/project_requirements.txt')
    r_file.to_single_file(examples_path / '.test_output.txt')
    assert Path(examples_path / '.test_output.txt').exists()
    