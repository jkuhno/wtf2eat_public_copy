# Custom errors

class RateLimitError(Exception):
    """Exception raised for API rate limit errors.

    Attributes:
        message -- explanation of the error
        provider -- API provider
    """

    def __init__(self, message, provider):
        self.message = message
        self.provider = provider
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} (From: {self.provider})'