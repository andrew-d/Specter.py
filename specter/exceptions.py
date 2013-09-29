class SpecterError(Exception):
    """Base class for all errors from Specter. """
    pass


class TimeoutError(SpecterError):
    """Error raised when a network operation times out."""
    pass


class InteractionError(SpecterError):
    """Error raised when there's no handlers listening for a prompt."""
    pass


class ElementError(SpecterError):
    """Error raised when Specter is unable to find an element."""
    pass
