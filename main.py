"""
Streamlit app for testing multi-threaded API calls with real-time progress display.
"""

import time
from datetime import datetime, timedelta

import streamlit as st

from api_simulator import SIMULATED_APIS, GeoBox, TimeRange
from thread_manager import APIStatus, ThreadManager


def main():
    st.set_page_config(
        page_title="Multi-API Query Test",
        page_icon="",
        layout="wide",
    )

    st.title("Multi-API Query Test")
    st.markdown("Test parallel API calls with real-time progress tracking.")

    # Initialize session state
    if "thread_manager" not in st.session_state:
        st.session_state.thread_manager = None
    if "query_running" not in st.session_state:
        st.session_state.query_running = False

    # Input form
    with st.form("query_form"):
        st.subheader("Query Parameters")

        # Query name
        query_name = st.text_input(
            "Query Name",
            value="My Query",
            help="A name to identify this query",
        )

        # Time range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=7),
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
            )

        # Geographic bounding box
        st.markdown("**Geographic Bounding Box**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            min_lat = st.number_input(
                "Min Latitude",
                value=34.0,
                min_value=-90.0,
                max_value=90.0,
                step=0.1,
                help="Lower-left corner latitude",
            )
        with col2:
            min_lon = st.number_input(
                "Min Longitude",
                value=-118.5,
                min_value=-180.0,
                max_value=180.0,
                step=0.1,
                help="Lower-left corner longitude",
            )
        with col3:
            max_lat = st.number_input(
                "Max Latitude",
                value=34.3,
                min_value=-90.0,
                max_value=90.0,
                step=0.1,
                help="Upper-right corner latitude",
            )
        with col4:
            max_lon = st.number_input(
                "Max Longitude",
                value=-118.0,
                min_value=-180.0,
                max_value=180.0,
                step=0.1,
                help="Upper-right corner longitude",
            )

        # Submit button
        submitted = st.form_submit_button(
            "Run Query",
            type="primary",
            use_container_width=True,
        )

    # Handle form submission
    if submitted and not st.session_state.query_running:
        # Validate inputs
        if min_lat >= max_lat:
            st.error("Min latitude must be less than max latitude")
        elif min_lon >= max_lon:
            st.error("Min longitude must be less than max longitude")
        elif start_date >= end_date:
            st.error("Start date must be before end date")
        else:
            # Create query parameters
            time_range = TimeRange(
                start=datetime.combine(start_date, datetime.min.time()),
                end=datetime.combine(end_date, datetime.max.time()),
            )
            geo_box = GeoBox(
                min_lat=min_lat,
                min_lon=min_lon,
                max_lat=max_lat,
                max_lon=max_lon,
            )

            # Start the query
            st.session_state.thread_manager = ThreadManager()
            st.session_state.thread_manager.submit_all(
                apis=SIMULATED_APIS,
                query_name=query_name,
                time_range=time_range,
                geo_box=geo_box,
            )
            st.session_state.query_running = True
            st.rerun()

    # Display progress if query is running
    if st.session_state.query_running and st.session_state.thread_manager:
        st.divider()
        st.subheader("API Progress")

        manager = st.session_state.thread_manager

        # Create status containers for each API
        status_containers = {}
        for api in SIMULATED_APIS:
            status_containers[api.name] = st.empty()

        # Poll and update until complete
        while not manager.is_complete():
            tasks = manager.get_tasks()

            for api_name, container in status_containers.items():
                task = tasks.get(api_name)
                if task:
                    _render_task_status(container, task)

            time.sleep(0.1)

        # Final render after completion
        tasks = manager.get_tasks()
        for api_name, container in status_containers.items():
            task = tasks.get(api_name)
            if task:
                _render_task_status(container, task)

        # Mark as complete
        st.session_state.query_running = False
        manager.shutdown()

        # Display results
        st.divider()
        st.subheader("Results")

        success_count = sum(
            1 for t in tasks.values()
            if t.status == APIStatus.SUCCESS
        )
        error_count = sum(
            1 for t in tasks.values()
            if t.status == APIStatus.ERROR
        )

        st.markdown(
            f"**Summary:** {success_count} successful, {error_count} failed"
        )

        for api_name, task in tasks.items():
            if task.status == APIStatus.SUCCESS and task.result and task.result.data:
                with st.expander(f"{api_name} - Results", expanded=False):
                    st.json(task.result.data)
            elif task.status == APIStatus.ERROR and task.result:
                with st.expander(f"{api_name} - Error", expanded=False):
                    st.error(task.result.error)


def _render_task_status(container, task):
    """Render the status of a single task in its container."""
    api_name = task.api.name
    status = task.status
    elapsed = task.elapsed_time_str

    if status == APIStatus.PENDING:
        container.info(f"**{api_name}** - Waiting...", icon="\u23f3")
    elif status == APIStatus.RUNNING:
        container.warning(f"**{api_name}** - Running... ({elapsed})", icon="\u23f1\ufe0f")
    elif status == APIStatus.SUCCESS:
        container.success(f"**{api_name}** - Completed ({elapsed})", icon="\u2705")
    elif status == APIStatus.ERROR:
        error_msg = task.result.error if task.result else "Unknown error"
        container.error(
            f"**{api_name}** - Failed ({elapsed}): {error_msg}",
            icon="\u274c"
        )


if __name__ == "__main__":
    main()
