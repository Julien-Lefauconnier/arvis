# arvis/timeline/timeline_view_types.py

from enum import Enum


class TimelineViewRole(str, Enum):
    """
    Declarative roles for timeline views.

    Roles define how a timeline is exposed:
    - no content
    - no reasoning
    - IRG-safe
    """

    TRACE_FACTUAL = "trace_factual"
    PUBLIC = "public"
    EXPOSED = "exposed"
    USER_VISIBLE = "user_visible"