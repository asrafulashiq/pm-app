"""Weekly summary view component."""

import streamlit as st
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pm.web.data_loader import WeeklyJournalData


def render_summary_view(journal_data: "WeeklyJournalData"):
    """Render weekly summary statistics.

    Args:
        journal_data: Weekly journal data with totals
    """
    # Calculate completion rate
    if journal_data.total_planned > 0:
        completion_rate = (journal_data.total_completed / journal_data.total_planned) * 100
    else:
        completion_rate = 0

    # Stats row using columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📅 Period",
            value=journal_data.week_range_str[:12] + "...",
            help=journal_data.week_range_str
        )

    with col2:
        st.metric(
            label="📋 Planned",
            value=journal_data.total_planned
        )

    with col3:
        st.metric(
            label="✅ Completed",
            value=journal_data.total_completed
        )

    with col4:
        # Color the completion rate
        if completion_rate >= 80:
            delta_color = "normal"
        elif completion_rate >= 50:
            delta_color = "off"
        else:
            delta_color = "inverse"

        st.metric(
            label="📈 Progress",
            value=f"{completion_rate:.0f}%",
            delta=None,
            delta_color=delta_color
        )
