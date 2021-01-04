class Error(Exception):
    """"""

    """Base class for other exceptions"""
    pass


class InvalidAuthTypeError(Error):
    """Exception raised for errors in the input salary.

    Attributes:
        auth_type -- sftp authorization type
        message -- explanation of the error
    """

    def __init__(self, auth_type, message="Auth type not supported."):
        self.auth_type = auth_type
        self.message = message
        super().__init__(self.message)


class FileListEmptyError(Error):
    """Raised when the input file list has no members"""

    pass


class BinarySecretError(Error):
    """Raised when non-String secrets are returned from SSM"""

    def __init__(self, message="Binary Secret not supported."):

        self.message = message
        super().__init__(self.message)

    pass
