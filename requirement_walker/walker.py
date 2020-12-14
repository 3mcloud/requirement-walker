"""
Class to parse requirements file.
1 Requirement should be on 1 line.
"""
# Built In
import re
import logging
from os.path import join
from pathlib import Path
from typing import Union, List, Generator
from pkg_resources import Requirement, RequirementParseError

# 3rd Party

# Owned

LOGGER = logging.getLogger(__name__)

# Used to seperate the important part from the comments on each line.
LINE_COMMENT_PATTERN = re.compile(r"^(?P<reqs>[^#\r\n]*?)(?:\s*)(?P<comment>#.*)?$")

# Used to pull out -r or --requirement files
# Works for multi `-r`s in a single line
# WORKS: -r test.txt -r ./path/test2.txt --requirement=oops.txt --requirement  C:\oops.txt
# INVALID: -r=333 # this should not match
REQ_OPTION_PATTERN = re.compile(r"(?:^|\s)(?P<option>(?:-r\s+)|((?:--requirement)(?:\s+|\=)))(?P<file_path>(?:.*?)(?=[\s]+|$))") # pylint: disable=line-too-long

# Pull out argument from comments for `requirement-walker`
# Example line in req file:
# my-req==1.1.1 # requirement-parse: local-package-name=my_package
ARG_EXTRACT_PATTERN = re.compile(r"(?:requirement-walker:\s*)(?P<args>.*)(?:\s|$)")


def read_file_lines(file_path: str):
    """
    Generator: opens the file and returns its line iterator.
    """
    with open(file_path, 'r') as file_obj:
        for line in file_obj:
            yield line

class RequirementFileError(Exception):
    """
    An exception raised when we try to parse a requirement which is
    a -r or --requirement flag.
    """

class Comment:
    """
    Class which represents a commment in the requirements file.
    """
    def __init__(self, comment_str: Union[str, None]):
        """
        Constructor
        ARGS:
            comment_str (str): A string which represent a comment in the requirements.txt
                file. The comment should start with `#`.
        """
        self._comment_str = comment_str
         # Stripping for good measure
        self.comment = comment_str.strip() if comment_str is not None else None
        self.arguments = self._extract_arguments() if self.comment else {}
        LOGGER.debug("Arguments pulled from comment: %s", self.arguments)

    def __bool__(self):
        """ A Comment is true if it is not `None` """
        return self.comment is not None

    def __repr__(self):
        """ TODO """
        return f"Comment(comment='{self.comment}')"

    def __str__(self):
        """ Return string representation of comment"""
        return self.comment

    def _extract_arguments(self) -> None:
        """
        Given a comment string, returns any requirement-walker arguments
        Example comments:
            # requirement-walker: local-package-name=my-local-package
          Or two arguments
            # requirement-walker: local-package-name=my-local-package|ignore-some=1,2,3
        Return a dict where each key is the name of an argument provided and the value
        is the value provided.
        Example:
        {
            "local-package-name": "my-local-package"
        }
        {
            "local-package-name: "my-local-package",
            "ignore-some": "1,2,3"
        }
        """
        supported_args = {
            # Arg name mapped to something (TBD)
            # For pip installing a local package. Value should be the name of the package so we can
            # name the requirement properly.
            'local-package-name',
            'root-relative',
        }
        extracted_args = {}
        search = ARG_EXTRACT_PATTERN.search(self.comment)
        if search:
            arg_str = search.group('args')
            for argument in arg_str.split('|'):
                name, *val = argument.split('=') # Pull the argument name from any assigned values.
                if name not in supported_args:
                    LOGGER.error("Unknown argument provided for requirement-walker: %s", name)
                    continue
                extracted_args[name] = val[0] if val else None
        return extracted_args

class LocalRequirement(Requirement):
    """
    Class to handle local requirements. Requirement name is optional
    but should probably be added.
    """
    def __init__(self, local_path, req_name: Union[str, None] = None):
        if req_name is None:
            req_name = 'local_req'
        super().__init__(req_name)
        self.url = local_path

class FailedRequirement(Requirement):
    """
    Class to handle failed requirements. Requirement name is optional
    but defaulted.
    """
    def __init__(self, full_req, req_name: Union[str, None] = None):
        if req_name is None:
            req_name = 'failed_req'
        super().__init__(req_name)
        self.url = full_req

class _ProxyRequirement: # pylint: disable=too-few-public-methods
    """
    Shoud resemble the pkg_resources.Requirement object. We either use that object or make one
    that looks similar when the parse for that one fails.
    """

    def __init__(self, requirement_str: Union[str, None], arguments: dict):
        """
        Constructor
        ARGS:
            requirement_str (str): The string which contains the requirement specification.
                Should NOT contain any comments.
            arguments (dict): A dictionary of requirement-walker arguments that were optionally
                added to the comments of this requirement.
        """
        self._requirement_str = requirement_str
        # Stripping for good measure
        self.requirement_str = requirement_str.strip() if requirement_str else None
        self.arguments = arguments
        LOGGER.debug("Arguments for requirements. Requirements %s - Arguments %s",
                     self.requirement_str, self.arguments)
        if self.requirement_str:
            try:
                self.requirement = Requirement.parse(self.requirement_str)
            except RequirementParseError as err:
                LOGGER.warning(
                    "Was unable to use pkg_resources to parse requirement. "
                    "Attempting too parse using custom code. RequirementParseError for reference:"
                    " %s", err
                )
                if REQ_OPTION_PATTERN.search(self.requirement_str):
                    #  Line had -r or --requirement flags
                    raise RequirementFileError(
                        "This requirement is a requirement file, parse serperately.")
                if 'local-package-name' in self.arguments:
                    # Else lets see if local-package-name argument was added
                    self.requirement = LocalRequirement(
                        self.arguments.get('root-relative', self.requirement_str),
                        self.arguments.get('local-package-name')
                    )
                else:
                    LOGGER.warning(
                        "Unable to parse requirement. Doing simple "
                        "FailedRequirement where name=%s and url=%s. Open Issue in "
                        "GitHub to have this fixed.",
                        'failed_req', self.requirement_str)
                    self.requirement = FailedRequirement(full_req=self.requirement_str)

    def __bool__(self):
        """ Returns False if None or empty string was passed as the requirement string """
        return bool(self.requirement_str)

    def __repr__(self):
        """ Return object representation """
        return (
            "Requirement(requirement_str="
            f"{repr(self._requirement_str)}, arguments={self.arguments})"
        )

    def __str__(self):
        """
        Returns the string string representation of a requirement.
        """
        if isinstance(self.requirement, FailedRequirement):
            return self.requirement.url
        if isinstance(self.requirement, LocalRequirement):
            return self.requirement.url
        return self.requirement.url if self.requirement.url else str(self.requirement)

class Entry: # pylint: disable=too-few-public-methods
    """
    We define an `Entry` as a line within the requirement file which is either a
    requirement and/or comment. An entry can be a:
        - requirement + a comment
        - requirement only
        - comment only
    """
    def __init__(self,
                 requirement: _ProxyRequirement,
                 comment: Comment):
        self.proxy_requirement = requirement
        self.requirement = requirement.requirement if requirement else None
        self.comment = comment

    def __str__(self):
        """ String magic method overload to print out an entry as it appeared before. """
        if not self.comment:
            return str(self.proxy_requirement)
        if not self.proxy_requirement:
            return str(self.comment)
        return str(self.proxy_requirement) + ' ' + str(self.comment)


def walk(file_path: str) -> Generator[Entry, None, None]:
    """
    Walks a requirement file path and yields a GENERATOR of Entry objects.
    ARGS:
        file_path (str): looks something like `./myfiles/requirements.txt`
    TODO: How to handle duplicates?
    """
    full_path = Path(file_path)
    LOGGER.info("Walking requirements for file: %s", full_path.absolute())
    for line in read_file_lines(full_path):
        # Strip off the newlines to make things easier
        line = line.strip()
        if not line:
            continue # Empty lines will be skipped entirely.
        # Pull out the requirement (seperated from any comments)
        match = LINE_COMMENT_PATTERN.match(line)
        if not match:
            LOGGER.error(
                "Could not properly match the following line (continuing): %s",
                line
            )
            continue

        req_str, comment = match.group('reqs'), match.group('comment')
        comment = Comment(comment)
        try:
            requirement = _ProxyRequirement(req_str, comment.arguments)
            yield Entry(requirement, comment)
        except RequirementFileError:
            LOGGER.debug("Parsed requirement appears to be -r argument, recursing...")
            for result in REQ_OPTION_PATTERN.finditer(req_str):
                new_path = result.group('file_path')
                full_relative_path = full_path.parent.absolute() / new_path
                LOGGER.debug(
                    "Recursively calling requirement walker. line: %s - new_path: %s",
                    new_path, full_relative_path
                )
                yield from walk(full_relative_path)


def entries_to_file(entries: List[Entry], file_path: str) -> None:
    """ Saves a list of entries to a requirements.txt file. """
    print(entries, file_path)
    raise NotImplementedError


if __name__ == "__main__":
    FORMAT = '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    ENTRIES = walk('./example_reqs.txt')
    # for e in entries:
    #     print(str(e.requirement))
    #     break
    print(*ENTRIES, sep='\n')
