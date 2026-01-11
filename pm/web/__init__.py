"""Web UI module for PM app.

Provides a read-only Streamlit interface for viewing weekly journals.
"""

from .data_loader import JournalDataLoader

__all__ = ["JournalDataLoader"]
