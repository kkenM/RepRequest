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