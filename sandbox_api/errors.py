import json
from django.http import HttpResponse

class WarningError(Exception):
    def __init__(self, title: str, detail: str) -> None:
        self.title = title
        self.detail = detail

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "{" + f'"title":{self.title}, "detail":{self.details}' + "}"
    
    def dict(self) -> dict:
        return {"title": self.title, "detail": self.detail}
class FatalError(Exception):
    """Default handelable error."""
    def __init__(self, message: str, details: list, code: int) -> None:
        self.message = message
        self.code = code
        self.details = details
    
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'"message":{self.message}, "status":{self.code}'
    
    def __dict__(self) -> dict:
        context = {}
        context["message"] = self.message
        context["status"] = self.code
        if self.details:
            context["details"] = self.details
        return context

    def response(self) -> HttpResponse:
        return HttpResponse(
            json.dumps(self.__dict__()),
            status = self.code,
            content_type="application/json")
    
class LoaderError(FatalError):
    def __init__(self, message: str, details: list) -> None:
        super().__init__("Loader error : " + message, details, 500)
class LoaderInstanceError(FatalError):
    def __init__(self, details: str) -> None:
        super().__init__("Loader instance error", details, 400)

class LoaderContextError(FatalError):
    def __init__(self, details: str) -> None:
        super().__init__("Malformed context for Loader", details, 400)

class LoaderSandboxError(FatalError):
    def __init__(self, details: str) -> None:
        super().__init__("Sandbox error", details, 500)

class LoaderIncludeError(FatalError):
    def __init__(self, details: str) -> None:
        super().__init__("Loader file error", details, 500)

class MissingFile(WarningError):
    def __init__(self, detail: str) -> None:
        super().__init__("Missing file", detail)