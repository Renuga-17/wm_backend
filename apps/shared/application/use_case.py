from abc import ABC, abstractmethod
from typing import Generic, TypeVar

RequestType = TypeVar('RequestType')
ResponseType = TypeVar('ResponseType')

class UseCase(ABC, Generic[RequestType, ResponseType]):
    """
    Interface for all Application Use Cases.
    An application use case orchestrates domain entities, services,
    and repositories to execute a specific business transaction.
    """
    @abstractmethod
    def execute(self, request: RequestType) -> ResponseType:
        """
        Execute the use case logic with the given request DTO.
        """
        pass
