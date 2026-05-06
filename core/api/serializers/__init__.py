from .account import AccountSerializer
from .activity import ActivitySerializer
from .contact import ContactSerializer
from .deal import DealContactAssocSerializer, DealSerializer
from .task import TaskSerializer

__all__ = [
    "AccountSerializer",
    "ActivitySerializer",
    "ContactSerializer",
    "DealContactAssocSerializer",
    "DealSerializer",
    "TaskSerializer",
]
