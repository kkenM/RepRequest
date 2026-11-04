"""
Business-logic exceptions used by RepRequest services.

Routes may catch these exceptions and decide how the error
should be presented to the user.
"""


class ServiceError(Exception):
    """
    Base exception for service-layer errors.
    """

    pass


class DuplicateEmailError(ServiceError):
    """
    Raised when an email address is already assigned
    to another RepRequest account.
    """

    pass


class InvalidEmployeeRoleError(ServiceError):
    """
    Raised when an invalid role is assigned to an employee.
    """

    pass

class DuplicateAssetTagError(Exception):
    """Asset tag is already used by another machine in this company."""

class InvalidRepairRequestError(ServiceError):
    """
    Raised when a repair request has an invalid severity or description,
    or names a machine that doesn't belong to the reporting user's company.
    The message is safe to show to the user.
    """

    pass


class AssignmentNotAllowedError(ServiceError):
    """
    Raised when a user tries to assign a repair request in a way their
    role doesn't permit, such as a technician assigning someone else.
    """

    pass
