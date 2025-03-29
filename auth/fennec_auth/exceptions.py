class FennecAuthException(Exception):
    pass


class AlreadyRegisteredUser(FennecAuthException):
    pass


class AlreadyRegisteredGroup(FennecAuthException):
    def __init__(self, group_name: str) -> None:
        self.group_name = group_name


class AlreadyRegisteredClientApplication(FennecAuthException):
    pass


class AlreadyAttachedPermission(FennecAuthException):
    pass


class GroupNotFound(FennecAuthException):
    def __init__(self, group_name: str) -> None:
        self.group_name = group_name


class ClientApplicationNotFound(FennecAuthException):
    pass


class PermissionNotFound(FennecAuthException):
    pass
