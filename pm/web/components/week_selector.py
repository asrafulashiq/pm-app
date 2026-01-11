"""Week selector component for navigation."""

import streamlit as st
from typing import List, Tuple


def render_week_selector(
    available_weeks: List[Tuple[int, int, str]],
    current_year: int,
    current_week: int
) -> Tuple[int, int]:
    """Render week selector in sidebar.

    Args:
        available_weeks: List of (year, week, display_string) tuples
        current_year: Current year
        current_week: Current ISO week number

    Returns:
        Selected (year, week) tuple
    """
    st.subheader("Select Week")

    # Initialize session state if needed
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = current_year
    if 'selected_week' not in st.session_state:
        st.session_state.selected_week = current_week

    # Quick navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Current", use_container_width=True, help="Go to current week"):
            st.session_state.selected_year = current_year
            st.session_state.selected_week = current_week
            st.rerun()

    with col2:
        if st.button("Previous", use_container_width=True, help="Go to previous week"):
            # Calculate previous week
            if st.session_state.selected_week > 1:
                st.session_state.selected_week -= 1
            else:
                st.session_state.selected_year -= 1
                st.session_state.selected_week = 52
            st.rerun()

    # Dropdown for all available weeks
    if available_weeks:
        # Create display options
        options = [w[2] for w in available_weeks]

        # Find default index based on session state
        default_idx = 0
        for idx, (year, week, _) in enumerate(available_weeks):
            if year == st.session_state.selected_year and week == st.session_state.selected_week:
                default_idx = idx
                break

        selected_option = st.selectbox(
            "Available Weeks",
            options=options,
            index=default_idx,
            key="week_dropdown"
        )

        # Find selected week from option
        for year, week, display in available_weeks:
            if display == selected_option:
                st.session_state.selected_year = year
                st.session_state.selected_week = week
                return year, week

    # Fallback to session state values
    return st.session_state.selected_year, st.session_state.selected_week
