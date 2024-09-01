from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND


class APIResponse(Response):
    """Custom response"""

    def __init__(
        self,
        data={},
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
        message="",
    ):
        self.message = message
        self.data = data
        self.configure_response()
        super().__init__(
            self.data, status, template_name, headers, exception, content_type
        )

    def configure_response(self) -> None:
        """Setting error and message in response body"""
        if self.message:
            self.data.update({"message": self.message})


class ErrorAPIResponse(Response):
    """Custom error response"""

    def __init__(
        self,
        data={},
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
        message="",
    ):
        self.message = message
        self.data = data
        self.configure_response()
        super().__init__(
            self.data, status, template_name, headers, exception, content_type
        )

    def configure_response(self) -> None:
        """Setting error and message in response body"""
        self.data = {"error": self.message}
