class FennecAuthException(Exception):
    pass


class AlreadyRegisteredUser(FennecAuthException):
    pass


class AlreadyRegisteredGroup(FennecAuthException):
    pass


class AlreadyRegisteredClientApplication(FennecAuthException):
    pass


class AlreadyAttachedPermission(FennecAuthException):
    pass


class GroupNotFound(FennecAuthException):
    pass


class ClientApplicationNotFound(FennecAuthException):
    pass


class PermissionNotFound(FennecAuthException):
    pass
