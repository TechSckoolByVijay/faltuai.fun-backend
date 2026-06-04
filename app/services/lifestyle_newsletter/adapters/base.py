"""
Base adapter interface for all content sources.
Every source adapter must inherit SourceAdapter and implement fetch().
"""
from __future__ import annotations

import abc
from typing import List

from app.schemas.lifestyle_newsletter import NormalizedContent


class SourceAdapter(abc.ABC):
    """Abstract base class for all Lifestyle Newsletter content source adapters."""

    source_name: str = "unknown"

    @abc.abstractmethod
    async def fetch(self) -> List[NormalizedContent]:
        """Fetch and normalise content from the source.

        Returns a list of NormalizedContent items. An empty list is valid
        (e.g., source is down or returns nothing relevant).
        """
        ...
