"""
Example code on how to read a requirements file and convert ssh requirements to https.
Useful for trying to download requirements from SSH but falling back to HTTPS.
"""
# Bult In
import re
import logging
import subprocess
from functools import lru_cache
from shutil import which

# 3rd Party
from requirement_walker import walk

# Owned

# Used to pull out the ssh domain to see if we have access to it.
EXTRACT_SSH_DOMAIN = re.compile(r"(?<=ssh://)(.*?)(?=/)")

# Used to pull out the leading ssh part so we can swap it with https.
MATCH_SSH = re.compile(r'ssh://git@')

LOGGER = logging.getLogger(__name__)

@lru_cache(maxsize=32)
def has_ssh(ssh_domain: str) -> bool:
    """
    Check that the user has ssh access to the given ssh domain
    First it will verify if ssh is installed in $PATH
    then check if we can authenticate to ssh_domain
    over ssh. Returns False if either of these are untrue

    Example ssh_domain: git@github.com
    """
    result = None
    if which('ssh') is not None:
        result = subprocess.Popen(['ssh', '-Tq', ssh_domain, '2>', '/dev/null'])
        result.communicate()
    if not result or result.returncode == 255:
        return False
    return True

def ssh_check_or_https(input_file_path: str, output_file_path: str) -> None:
    """
    Given a path to q requirements file, will look for SSH requirements. If this terminal
    does not have access to that SSH domain then it will change the requirement to HTTPs.
    Can handle referencing other requirement files BUT will output all requirements to a SINGLE
    requirement file.
    ARGS:
        input_file_path (str): Path to the inputted requirements.txt file.
        output_file_path (str): Path to output all the requirements to.
    All requirements will be output 
    """

    entries = []
    for entry in walk(input_file_path):
        if entry.requirement.url:
            ssh_domain = EXTRACT_SSH_DOMAIN.search(entry.requirement.url)
            if ssh_domain and not has_ssh(ssh_domain.group(1)):
                new_url = MATCH_SSH.sub('https://', entry.requirement.url)
                LOGGER.info(
                    "No access to domain %s:\n"
                    "       Swapping:\n"
                    "           - %s\n"
                    "       For:\n"
                    "           - %s\n", ssh_domain.group(1), entry.requirement.url, new_url)
                entry.requirement.url = new_url
        entries.append(entry)

    with open(output_file_path, 'w') as req_file:
        req_file.writelines((str(entry) + '\n' for entry in entries))
