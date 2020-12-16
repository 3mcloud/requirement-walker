""" Regular Expressions used for parsing. """

# Built In
import re

# 3rd Party

# Owned

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

# Used to see if a requirement is a git URL and if so, remove the protocol.
GIT_PROTOCOL = re.compile(r"(?:git\+)(?P<protocol>ssh|http|https)(?::\/\/)")
