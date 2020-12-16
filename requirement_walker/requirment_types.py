"""
Different types of requirements which are children of the `Requirement` object but used
to handle requirements not natively supported by `Requirement`
"""

# Built In
from pkg_resources import Requirement
from typing import Union

# 3rd Party

# Owned


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
