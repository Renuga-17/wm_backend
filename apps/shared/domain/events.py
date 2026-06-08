import datetime
import uuid
from dataclasses import dataclass, field

@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all Domain Events.
    A Domain Event is something that happened in the domain that you care about.
    """
    event_id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)
    occurred_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), init=False)
