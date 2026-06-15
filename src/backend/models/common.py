from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class DecisionStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


DatetimeLike = datetime
