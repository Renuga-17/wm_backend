from contextvars import ContextVar
from typing import Optional
import uuid

# ContextVar is thread-safe and async-safe
_current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar('current_tenant_id', default=None)

class TenantContext:
    """
    Thread-safe and async-safe context manager to store and retrieve
    the active tenant ID throughout the lifecycle of a request.
    """
    @staticmethod
    def set_current_tenant_id(tenant_id: uuid.UUID) -> None:
        """
        Bind a tenant ID to the current thread/execution context.
        """
        if not isinstance(tenant_id, uuid.UUID):
            try:
                tenant_id = uuid.UUID(str(tenant_id))
            except ValueError:
                raise ValueError("Tenant ID must be a valid UUID")
        _current_tenant_id.set(tenant_id)

    @staticmethod
    def get_current_tenant_id() -> Optional[uuid.UUID]:
        """
        Retrieve the current tenant ID, if bound.
        """
        return _current_tenant_id.get()

    @staticmethod
    def clear() -> None:
        """
        Clear the tenant ID context.
        """
        _current_tenant_id.set(None)
