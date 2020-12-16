"""
Different types of requirements which are children of the `Requirement` object but used
to handle requirements not natively supported by `Requirement`
"""

# Built In
from typing import Union
from pkg_resources import Requirement

# 3rd Party

# Owned


class LocalPackageRequirement(Requirement): # pylint: disable=too-few-public-methods
    """
    Class to handle local requirements. Requirement name is optional
    but should probably be added.
    """
    def __init__(self, local_path, req_name: Union[str, None] = None):
        if req_name is None:
            req_name = 'local_req'
        super().__init__(req_name)
        self.url = local_path

    def __bool__(self):
        """ Requirements will be considered true by nature. """
        return True

class FailedRequirement(Requirement): # pylint: disable=too-few-public-methods
    """
    Class to handle failed requirements. Requirement name is optional
    but defaulted.
    """
    def __init__(self, full_req, req_name: Union[str, None] = None):
        if req_name is None:
            req_name = 'failed_req'
        super().__init__(req_name)
        self.url = full_req

    def __bool__(self):
        """ Requirements will be considered true by nature. """
        return True
