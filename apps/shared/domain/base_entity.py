import uuid
from dataclasses import dataclass, field
from typing import Any, List, Set

@dataclass
class ValueObject:
    """
    An immutable object whose equality is based on its values rather than identity.
    """
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


@dataclass
class Entity:
    """
    An object defined by its identity (id) rather than its attributes.
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class AggregateRoot(Entity):
    """
    An entity that acts as the entrypoint for aggregate state changes,
    responsible for tracking and raising domain events.
    """
    _domain_events: List[Any] = field(default_factory=list, init=False, repr=False)

    def record_event(self, event: Any) -> None:
        """
        Record a domain event to be dispatched later when changes are persisted.
        """
        self._domain_events.append(event)

    def clear_events(self) -> None:
        """
        Clear all recorded domain events.
        """
        self._domain_events.clear()

    @property
    def domain_events(self) -> List[Any]:
        """
        Retrieve all recorded domain events.
        """
        return list(self._domain_events)
