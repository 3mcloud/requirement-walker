""" Module level imports. Moving stuff up. """
from .walker import Entry, Comment, _ProxyRequirement, RequirementFile
from .requirment_types import LocalRequirement, FailedRequirement
from .regex_expressions import (
    LINE_COMMENT_PATTERN, # Serpate a requirement from its comments.
    REQ_OPTION_PATTERN, # Extract -r and --requirement from a requirement.
    ARG_EXTRACT_PATTERN, # Extract package arguments from the requirement comments.
    GIT_PROTOCOL # Extra git protocal from git requirements.
)