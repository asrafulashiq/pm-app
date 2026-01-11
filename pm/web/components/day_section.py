"""Day section component for displaying daily journal entries."""

import streamlit as st
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pm.web.data_loader import DaySectionData, TaskDisplayData


def render_task_item(task: "TaskDisplayData", status_icon: str = ""):
    """Render a single task item.

    Args:
        task: Task data to display
        status_icon: Icon to show (checkbox, blocked, etc.)
    """
    # Priority colors (using Unicode emojis)
    priority_colors = {
        "high": "🔴",
        "medium": "🟠",
        "low": "🟢"
    }
    priority_icon = priority_colors.get(task.priority, "")

    # Status indicator
    if task.is_completed:
        title_style = f"~~{task.title}~~"
        status_icon = "✅"
    else:
        title_style = task.title

    # Build task display
    st.markdown(f"{status_icon} {priority_icon} **{title_style}**")
    st.caption(f"`{task.id}` | {task.type} | {task.priority}" +
               (f" | ETA: {task.eta}" if task.eta else ""))


def render_day_section(day_data: "DaySectionData", expanded: bool = False):
    """Render a single day's journal section.

    Args:
        day_data: Day section data to display
        expanded: Whether to expand by default
    """
    # Count tasks for the header
    task_count = len(day_data.planned_tasks)
    completed_count = len(day_data.completed_tasks)
    blocked_count = len(day_data.blocked_tasks)

    # Build header with counts
    header = f"**{day_data.day_name}, {day_data.date_str}**"
    if task_count > 0:
        header += f" ({completed_count}/{task_count} done"
        if blocked_count > 0:
            header += f", {blocked_count} blocked"
        header += ")"

    # Use expander for each day
    with st.expander(header, expanded=expanded):
        if not day_data.planned_tasks and not day_data.blocked_tasks:
            st.caption("No tasks for this day")
        else:
            # Task sections in columns
            col1, col2 = st.columns(2)

            with col1:
                # Planned tasks (not completed)
                pending = [t for t in day_data.planned_tasks if not t.is_completed]
                if pending:
                    st.markdown("##### 📋 Planned")
                    for task in pending:
                        render_task_item(task, "⚪")

                # Blocked tasks
                if day_data.blocked_tasks:
                    st.markdown("##### 🚫 Blocked")
                    for task in day_data.blocked_tasks:
                        render_task_item(task, "⚠️")

            with col2:
                # Completed tasks
                if day_data.completed_tasks:
                    st.markdown("##### ✅ Completed")
                    for task in day_data.completed_tasks:
                        render_task_item(task)

                # In Progress tasks
                if day_data.in_progress_tasks:
                    st.markdown("##### 🔄 In Progress")
                    for task in day_data.in_progress_tasks:
                        if not task.is_completed:
                            render_task_item(task, "🔵")

        # Notes section
        if day_data.notes and day_data.notes.strip():
            st.markdown("---")
            st.markdown("##### 📝 Notes")
            st.markdown(day_data.notes)
