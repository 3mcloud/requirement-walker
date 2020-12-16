"""
Package to parse requirements file.
"""

# Built In
import logging
from pathlib import Path
from typing import Union, Generator, Tuple
from pkg_resources import Requirement

# 3rd Party

# Owned
from .requirment_types import LocalPackageRequirement, FailedRequirement
from .regex_expressions import (
    LINE_COMMENT_PATTERN, # Serpate a requirement from its comments.
    REQ_OPTION_PATTERN, # Extract -r and --requirement from a requirement.
    ARG_EXTRACT_PATTERN, # Extract package arguments from the requirement comments.
    GIT_PROTOCOL # Extra git protocal from git requirements.
)

LOGGER = logging.getLogger(__name__)

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
        self.comment = comment_str.strip() if isinstance(comment_str, str) else None
        self.arguments = self._extract_arguments() if self.comment else {}
        LOGGER.debug("Arguments pulled from comment: %s", self.arguments)

    def __bool__(self):
        """
        A Comment is true if it is not `None` (an empty string comment would still return True)
        """
        return self.comment is not None

    def __repr__(self) -> str:
        """ TODO """
        if self:
            return f"Comment(comment='{self.comment}')"
        return "Comment(comment=None)"

    def __str__(self) -> str:
        """
        Return string representation of comment (i.e. what was before) including the #.
        If there was no comment, then this will just return an empty string
        """
        if self:
            return self.comment
        return ''

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
        self.requirement_str = requirement_str.strip() if isinstance(requirement_str, str) else None
        self.arguments = arguments
        LOGGER.debug("Arguments for requirements. Requirements %s - Arguments %s",
                     self.requirement_str, self.arguments)
        if self.requirement_str:
            try:
                self.requirement = Requirement.parse(self.requirement_str)
            except Exception as err: # pylint: disable=broad-except
                LOGGER.info(
                    "Was unable to use pkg_resources to parse requirement. "
                    "Attempting too parse using custom code. Exception for reference:"
                    " %s", err
                )
                if REQ_OPTION_PATTERN.search(self.requirement_str):
                    #  Line had -r or --requirement flags
                    raise RequirementFileError(
                        "This requirement is a requirement file, parse serperately.") from None
                if 'local-package-name' in self.arguments:
                    # Else lets see if local-package-name argument was added
                    self.requirement = LocalPackageRequirement(
                        self.arguments.get('root-relative', self.requirement_str),
                        self.arguments.get('local-package-name')
                    )
                else:
                    # Couldn't parse it with our current logic.
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
        if isinstance(self.requirement, LocalPackageRequirement):
            return self.requirement.url
        return str(self.requirement) # Fall back to the string representation of a Requirement

class Entry: # pylint: disable=too-few-public-methods
    """
    We define an `Entry` as a line within the requirement file.
    An entry can be a:
        - requirement + a comment
        - requirement only
        - comment only
        - empty line
        - requirement file (multiple can be in one line but it will be flattened)
        - requirement file + a comment
    Ideally, if you iterate over each entry and add each one to a file you will
    end with all your requirements in a single file with the same formatting they were pulled as.
    """
    def __init__(self,
                 *_, # Not going to allow positional arguments.
                 proxy_requirement: Union['_ProxyRequirement', None] = None,
                 comment: ['Comment', None] = None,
                 requirement_file: Union['RequirementFile', None] = None):
        self.proxy_requirement = proxy_requirement if proxy_requirement else None
        self.requirement = proxy_requirement.requirement if proxy_requirement else None
        self.comment = comment if comment else None
        self.requirement_file = requirement_file

    def __str__(self):
        """ String magic method overload to print out an entry as it appeared before. """
        root_relative = self.comment.arguments.get('root-relative', None) if self.comment else None
        # pylint: disable=line-too-long
        str_map = {
            # proxy_requirement, comment, requirement_file
            (False, False, False): '', # Was just an empty line
            (True, False, False): f"{self.proxy_requirement}",
            (False, True, False):  f"{self.comment}",
            (False, False, True): f"-r {root_relative}" if root_relative else f"-r {self.requirement_file}",
            (True, True, False): f"{self.proxy_requirement} {self.comment}",
            (False, True, True): f"-r {root_relative} {self.comment}" if root_relative else f"-r {self.requirement_file} {self.comment}",
        }
        # pylint: enable=line-too-long
        key = (bool(self.proxy_requirement), bool(self.comment), bool(self.requirement_file))
        try:
            return str_map[key]
        except KeyError:
            LOGGER.exception(
                "Exception occured. Unknown pattern of arguments passed to Entry object.Continueing"
            )
            return ''

    def __bool__(self):
        """
        A Entry is considered False if it was just an empty line or a line with nothing
        but spaces.
        """
        for attr in (self.proxy_requirement, self.comment, self.requirement_file):
            if attr is not None:
                return True
        return False

    def is_git(self, return_protocol: bool = False) -> Union[bool, Tuple[bool, str]]:
        """
        Returns true if the requirement for this entry is a requirement to a git URL.
        ARGS:
            return_protocol (bool): If set to True instead of just return a bool, this method
                will also return the protocol used for git: ['http', 'https', 'ssh', '']
        """
        if self.requirement and self.requirement.url:
            result = GIT_PROTOCOL.search(self.requirement.url)
            if result:
                return (True, result.group('protocol')) if return_protocol else True
        return (False, '') if return_protocol else False

    def is_comment_only(self):
        """ Returns true if this entry was a comment and nothing else. """
        for attr in (self.proxy_requirement, self.requirement_file):
            if attr is not None:
                return False
        if self.comment is None:
            return False
        return True

class RequirementFile:
    """ A class which represents a requirement file. """
    def __init__(self, requirement_file_path: str):
        """
        Constructor.
        ARGS:
            requirement_file_path (str): Path, absolute or relative, to a `requirements.txt` file.
        """
        self.sub_req_files = {}
        self.requirement_file_path = Path(requirement_file_path)
        self._entries = None

    @property
    def entries(self):
        """ Property, returns a list of all entries. """
        if self._entries is None:
            self._entries = list(self)
        return self._entries

    def to_single_file(self,
                       path: str,
                       np_duplicate_lines: bool = False,
                       no_empty_lines: bool = False,
                       no_comment_only_lines: bool = False) -> None:
        """
        Output all requirements to the provided path. Creates/overwrites the provided file path.
        Good for removing `-r` or `--requirement` flags.
        ARGS:
            path (str): Path to the file which will be written to.
            np_duplicate_lines (bool): Skips duplicate lines
                                       (Entire line must be a duplicate with another).
            no_empty_lines (bool): Don't add lines that were empty or just had spaces.
            no_comment_only_lines (bool): Don't add lines which were only comments with
                                          no requirements.
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True) # Make the directory if it doesn't exist
        entries_to_write = []
        for entry in self.iter_recursive():
            if no_empty_lines and not entry:
                continue
            if no_comment_only_lines and entry.is_comment_only():
                continue
            entries_to_write.append(entry)
        if np_duplicate_lines:
            entries_to_write = {val: None for val in entries_to_write} # Set doesn't retain order.
        with open(file_path.absolute(), 'w') as output_file:
            print(*entries_to_write, sep='\n', file=output_file)

    def __iter__(self) -> Generator[Entry, None, None]:
        """
        If no entries have been parsed yet, walks a requirement file path but if the class already
        has entries, then yields from existing entries. Yields a GENERATOR of Entry objects.
        """
        if isinstance(self._entries, list):
            LOGGER.debug("Yielding from cached entries.")
            for entry in self._entries:
                yield entry
            return

        LOGGER.info("Iterating requirements file: %s", self.requirement_file_path.absolute())
        with open(self.requirement_file_path.absolute()) as input_file:
            for line in input_file:
                # Strip off the newlines to make things easier
                line = line.strip()
                if not line:
                    yield Entry() # Empty Line
                    continue

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
                    yield Entry(proxy_requirement=requirement, comment=comment)
                except RequirementFileError:
                    LOGGER.debug(
                        "Parsed requirement appears to be -r argument, make entry a req file.")
                    for result in REQ_OPTION_PATTERN.finditer(req_str):
                        new_path = result.group('file_path')
                        full_relative_path = self.requirement_file_path.parent.absolute() / new_path
                        LOGGER.debug(
                            "Parent File: %s - Child requirement file "
                            "path: %s - New Child Path: %s",
                            self.requirement_file_path.parent.absolute(),
                            new_path,
                            full_relative_path
                        )
                        yield Entry(
                            requirement_file=RequirementFile(full_relative_path),
                            comment=comment
                        )
        return

    def __repr__(self):
        """ Object Representation """
        return f"RequirementFile(requirement_file_path='{self.requirement_file_path.absolute()}')"

    def __str__(self):
        """ String Overload, returns the absolute path to the req file. """
        return str(self.requirement_file_path.absolute())

    def iter_recursive(self,
                       no_empty_lines: bool = False,
                       no_comment_only_lines: bool = False) -> Generator[Entry, None, None]:
        """
        Iterates through requirements. If another requirement file is hit, it will yield
        from that generator.

        ARGS:
            path (str): Path to the file which will be written to.
            no_empty_lines (bool): Don't return lines that were empty or just had spaces.
            no_comment_only_lines (bool): Don't return lines which were only comments with
                                          no requirements.
        """
        for entry in self:
            if isinstance(entry.requirement_file, RequirementFile):
                yield from entry.requirement_file.iter_recursive()
            else:
                if no_empty_lines and not entry:
                    continue
                if no_comment_only_lines and entry.is_comment_only():
                    continue
                yield entry
