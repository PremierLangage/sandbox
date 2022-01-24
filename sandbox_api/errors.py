
class LoaderInstanceError(Exception):
    """Raised when type of files not expected."""

    def __init__(self, message: str, code: int) -> None:
        self.message = message
        self.code = code

    def __repr__(self) -> str:
        return f'"code":{self.code}, "message"="{self.message}"'

    def __str__(self) -> str:
        return """
        {
            "code":{self.code},
            "message":{self.message}
        }
        """
