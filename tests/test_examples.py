""" Simple testing based on the example in the README """

# Built In
from pathlib import Path

# 3rd Party
from requirement_walker import LocalPackageRequirement, FailedRequirement, RequirementFile

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
    assert len(entries) == 12
    # with open("temp.txt", 'w') as f:
    #     entries = [str(entry) + '\n' for entry in entries]
    #     f.writelines(entries)  

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
    r_file.to_single_file(examples_path.parent / 'test_output_files' / 'test_output_file.txt')
    assert Path(examples_path.parent / 'test_output_files' / 'test_output_file.txt').exists()

def test_output_file_ignore_empty_lines(examples_path):
    """ Try outputting requirements to a single  file """
    r_file = RequirementFile(examples_path / './example_application/project_requirements.txt')
    output_file_path = examples_path.parent / 'test_output_files' / 'test_output_file_ignore_empty_lines.txt'
    r_file.to_single_file( # First lets get the full file
        output_file_path,
    )
    base_line_count = 0
    with open(output_file_path) as file_obj:
        for _ in file_obj:
            base_line_count += 1

    r_file.to_single_file( # Now with no comment only lines
        output_file_path,
        no_comment_only_lines=True,
    )
    no_comment_only_count = 0
    with open(output_file_path) as file_obj:
        for _ in file_obj:
            no_comment_only_count += 1

    r_file.to_single_file( # Now with no comment only lines
        output_file_path,
        no_empty_lines=True,
    )
    no_empty_line_count = 0
    with open(output_file_path) as file_obj:
        for _ in file_obj:
            no_empty_line_count += 1

    r_file.to_single_file( # Now with no comment only lines
        output_file_path,
        no_comment_only_lines=True,
        no_empty_lines=True,
    )
    no_empty_line_or_comment_only_count = 0
    with open(output_file_path) as file_obj:
        for _ in file_obj:
            no_empty_line_or_comment_only_count += 1

    assert base_line_count == 26
    assert no_comment_only_count == 21
    assert no_empty_line_count == 23
    assert no_empty_line_or_comment_only_count == 18

def test_readme_output(examples_path):
    """ Get the first output for the README. """
    req_file = RequirementFile(examples_path / './example_application/project_requirements.txt')
    # RequirementFile has a magic method __iter__ written for it so it can be iterated over.
    print("Output 1:", *req_file, sep='\n') # Output found down below
    print("---------------------------------------------")
    print("Output 2:", *req_file.iter_recursive(), sep='\n') # Output found down below
    assert True

def test_readme_failed_req(examples_path):
    """ Get the second output for the README. """
    for entry in RequirementFile(examples_path / './requirements.txt'):
        if isinstance(entry.requirement, FailedRequirement):
            print("This requirement was a failed req.", entry)
        elif isinstance(entry.requirement, LocalPackageRequirement):
            print("This requirement was a local req.", entry)
        # If a entry is a requirement file, `requirement` will be None
        # and `requirement_file` will have a value other then None.
        elif isinstance(entry.requirement_file, RequirementFile):
            print("This entry is another requirement file.", entry)
    assert True
