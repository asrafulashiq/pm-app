"""Streamlit web application for PM weekly journals.

Read-only view of weekly journal entries with navigation and filtering.
"""

import streamlit as st
from datetime import datetime

from pm.web.data_loader import JournalDataLoader
from pm.web.components import render_week_selector, render_day_section, render_summary_view


def main():
    """Main Streamlit application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="PM Weekly Journal",
        page_icon="📓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better dark mode styling
    st.markdown("""
        <style>
        /* Metric cards */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }

        /* Expander headers */
        .streamlit-expanderHeader {
            font-size: 1.1rem;
            font-weight: 600;
        }

        /* Task items */
        .task-item {
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 6px;
            background-color: rgba(255, 255, 255, 0.05);
        }

        /* Priority indicators */
        .priority-high { border-left: 3px solid #ff4b4b; padding-left: 8px; }
        .priority-medium { border-left: 3px solid #ffa726; padding-left: 8px; }
        .priority-low { border-left: 3px solid #66bb6a; padding-left: 8px; }

        /* Completed tasks */
        .task-completed {
            opacity: 0.7;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: rgba(14, 17, 23, 0.95);
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize data loader
    loader = JournalDataLoader()

    # Sidebar - Week Selection
    with st.sidebar:
        st.title("📓 PM Journal")
        st.markdown("---")

        # Get available weeks and current week
        available_weeks = loader.get_available_weeks()
        current_year, current_week = loader.get_current_week()

        # Week selector
        selected_year, selected_week = render_week_selector(
            available_weeks,
            current_year,
            current_week
        )

        st.markdown("---")
        st.caption("Read-only view of weekly journals")
        st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")

        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Main content area
    st.title(f"Week {selected_week}, {selected_year}")

    # Load journal data
    journal_data = loader.get_journal_data(selected_year, selected_week)

    if journal_data is None:
        st.warning(f"No journal found for Week {selected_week}, {selected_year}")
        st.info("""
        Journals are created when you use the PM CLI:
        - `pm journal` - Open weekly journal in editor
        - `pm journal-start` - Initialize today's journal section
        """)

        # Show available weeks if any
        if available_weeks:
            st.markdown("### Available Journals")
            for year, week, display in available_weeks[:5]:
                st.markdown(f"- {display}")
        return

    # Week header with stats
    render_summary_view(journal_data)

    st.markdown("---")

    # Day filter - tabs for each day
    today = datetime.now()
    sorted_days = sorted(journal_data.days.items())

    # Create tab labels
    tab_labels = ["All Days"] + [
        f"{data.day_name[:3]} {data.date_str}"
        for _, data in sorted_days
    ]

    tabs = st.tabs(tab_labels)

    # All Days tab
    with tabs[0]:
        for day_key, day_data in sorted_days:
            # Expand today's section by default
            is_today = day_data.date.date() == today.date()
            render_day_section(day_data, expanded=is_today)

    # Individual day tabs
    for idx, (day_key, day_data) in enumerate(sorted_days):
        with tabs[idx + 1]:
            render_day_section(day_data, expanded=True)


if __name__ == "__main__":
    main()
