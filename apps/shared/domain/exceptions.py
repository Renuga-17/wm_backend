class WmsDomainException(Exception):
    """
    Base exception for all domain-specific business rule violations.
    Inherited by exceptions across all bounded contexts.
    """
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
