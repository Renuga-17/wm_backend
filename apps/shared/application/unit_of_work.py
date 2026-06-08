from abc import ABC, abstractmethod
from typing import Any

class IUnitOfWork(ABC):
    """
    Interface for the Unit of Work pattern.
    Ensures that multiple repository actions and outbox event writings
    commit or rollback as a single transaction.
    """
    def __enter__(self) -> 'IUnitOfWork':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self) -> None:
        """
        Commit current transaction and dispatch/store pending domain events.
        """
        pass

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback the current transaction.
        """
        pass
