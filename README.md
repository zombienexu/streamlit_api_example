# Streamlit Multi-API App

A Streamlit application that executes multiple API calls in parallel threads with real-time progress tracking.

## Running the App

```bash
uv run streamlit run main.py
```

Then open http://localhost:8501 in your browser.

## Architecture Overview

```
main.py              # Streamlit UI - input form and progress display
thread_manager.py    # ThreadManager class - orchestrates parallel API calls
api_simulator.py     # SimulatedAPI definitions and mock API functions
```

## How the Thread Manager Works

The `ThreadManager` class in `thread_manager.py` orchestrates parallel API execution using Python's `concurrent.futures.ThreadPoolExecutor`.

### Core Components

**1. APIStatus Enum**
Tracks the lifecycle of each API call:
- `PENDING` - Task created but not started
- `RUNNING` - API call in progress
- `SUCCESS` - Completed successfully
- `ERROR` - Failed with an error

**2. APITask Dataclass**
Holds state for a single API task:
- `api` - The SimulatedAPI configuration
- `status` - Current APIStatus
- `start_time` / `end_time` - Timestamps for elapsed time calculation
- `result` - The APIResult after completion

**3. ThreadManager Class**
The main orchestrator with these key methods:

```python
# Submit all API calls to run in parallel
manager.submit_all(apis, query_name, time_range, geo_box)

# Get current status of all tasks (thread-safe snapshot)
tasks = manager.get_tasks()

# Check if all tasks have completed
if manager.is_complete():
    ...

# Clean up the thread pool
manager.shutdown()
```

### Execution Flow

1. `submit_all()` creates an `APITask` for each API in `PENDING` state
2. Each API is submitted to the `ThreadPoolExecutor` as a separate thread
3. `_run_task()` runs in each thread:
   - Sets status to `RUNNING` and records `start_time`
   - Calls `simulate_api_call()` (or your real API)
   - Sets status to `SUCCESS` or `ERROR` and records `end_time`
4. The Streamlit UI polls `get_tasks()` every 100ms to update the display
5. When `is_complete()` returns True, results are displayed

### Thread Safety

All task state updates use a `threading.Lock` to prevent race conditions:

```python
with self._lock:
    task.status = APIStatus.RUNNING
    task.start_time = time.time()
```

---

## Adding More APIs

### Step 1: Define the API in `api_simulator.py`

Add a new `SimulatedAPI` to the `SIMULATED_APIS` list:

```python
SIMULATED_APIS = [
    # ... existing APIs ...

    SimulatedAPI(
        name="My New API",
        min_duration=2.0,    # Minimum response time in seconds
        max_duration=4.0,    # Maximum response time in seconds
        failure_rate=0.10,   # 10% chance of failure
    ),
]
```

### Step 2: Add Mock Data Generation

In `api_simulator.py`, update the `_generate_mock_data()` function:

```python
def _generate_mock_data(api_name, query_name, time_range, geo_box):
    base_data = { ... }

    # ... existing API handlers ...

    elif api_name == "My New API":
        base_data["my_data"] = {
            "field1": random.randint(1, 100),
            "field2": round(random.uniform(0, 1), 3),
        }

    return base_data
```

That's it! The new API will automatically appear in the UI and run in parallel with the others.

---

## Adding More Arguments to APIs

To add new user inputs that get passed to the API calls:

### Step 1: Add the Dataclass (if needed)

In `api_simulator.py`, define a new dataclass for structured data:

```python
@dataclass
class SearchFilters:
    """Additional search filters for API calls."""
    category: str
    min_value: float
    max_value: float
    include_historical: bool
```

### Step 2: Update the API Function Signature

Modify `simulate_api_call()` to accept the new parameter:

```python
def simulate_api_call(
    api: SimulatedAPI,
    query_name: str,
    time_range: TimeRange,
    geo_box: GeoBox,
    filters: SearchFilters,  # New parameter
) -> APIResult:
    # ... existing logic ...
```

Also update `_generate_mock_data()` if the new data should appear in results:

```python
def _generate_mock_data(api_name, query_name, time_range, geo_box, filters):
    base_data = {
        # ... existing fields ...
        "filters": {
            "category": filters.category,
            "min_value": filters.min_value,
            "max_value": filters.max_value,
            "include_historical": filters.include_historical,
        },
    }
```

### Step 3: Update ThreadManager

In `thread_manager.py`, update `submit_all()` and `_run_task()`:

```python
def submit_all(
    self,
    apis: list[SimulatedAPI],
    query_name: str,
    time_range: TimeRange,
    geo_box: GeoBox,
    filters: SearchFilters,  # New parameter
) -> None:
    # ... existing setup ...

    for api in apis:
        self._executor.submit(
            self._run_task,
            api,
            query_name,
            time_range,
            geo_box,
            filters,  # Pass to thread
        )

def _run_task(
    self,
    api: SimulatedAPI,
    query_name: str,
    time_range: TimeRange,
    geo_box: GeoBox,
    filters: SearchFilters,  # New parameter
) -> None:
    # ... existing logic ...
    result = simulate_api_call(api, query_name, time_range, geo_box, filters)
```

### Step 4: Add UI Inputs in `main.py`

Add input widgets inside the form:

```python
with st.form("query_form"):
    # ... existing inputs ...

    # New filter inputs
    st.markdown("**Search Filters**")
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Category",
            options=["residential", "commercial", "industrial"],
        )
        min_value = st.number_input("Min Value", value=0.0)
    with col2:
        max_value = st.number_input("Max Value", value=100.0)
        include_historical = st.checkbox("Include Historical Data")
```

Then create the dataclass and pass it to the thread manager:

```python
if submitted:
    # ... existing validation ...

    filters = SearchFilters(
        category=category,
        min_value=min_value,
        max_value=max_value,
        include_historical=include_historical,
    )

    st.session_state.thread_manager.submit_all(
        apis=SIMULATED_APIS,
        query_name=query_name,
        time_range=time_range,
        geo_box=geo_box,
        filters=filters,  # Pass new argument
    )
```

---

## Replacing Simulated APIs with Real APIs

To use real API calls instead of simulations:

### Option 1: Replace `simulate_api_call()`

Create a new function that makes actual HTTP requests:

```python
import requests

def call_real_api(
    api: SimulatedAPI,
    query_name: str,
    time_range: TimeRange,
    geo_box: GeoBox,
) -> APIResult:
    try:
        if api.name == "Weather API":
            response = requests.get(
                "https://api.weather.example.com/data",
                params={
                    "lat": geo_box.min_lat,
                    "lon": geo_box.min_lon,
                    "start": time_range.start.isoformat(),
                    "end": time_range.end.isoformat(),
                },
                timeout=30,
            )
            response.raise_for_status()
            return APIResult(success=True, data=response.json())

        # ... handle other APIs ...

    except requests.RequestException as e:
        return APIResult(success=False, error=str(e))
```

### Option 2: Use a Registry Pattern

For cleaner separation, create an API registry:

```python
API_HANDLERS = {
    "Weather API": fetch_weather_data,
    "Satellite Data API": fetch_satellite_data,
    # ...
}

def call_api(api: SimulatedAPI, **kwargs) -> APIResult:
    handler = API_HANDLERS.get(api.name)
    if handler:
        return handler(**kwargs)
    return APIResult(success=False, error=f"Unknown API: {api.name}")
```

Then update `_run_task()` in `thread_manager.py` to use this instead of `simulate_api_call()`.
