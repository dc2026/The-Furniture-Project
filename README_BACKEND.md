# Furniture Project Backend System

## Backend Files for Dashboard Integration

### Core Data Processing
- `clean_data.py` - Processes raw request data and categorizes by size
- `backend_api.py` - Main API endpoints for dashboard

### Scheduling & Optimization  
- `calendar_system.py` - Auto-populates calendar with available slots
- `route_assignment.py` - Assigns complete routes to trucks
- `zone_scheduling.py` - Groups orders by geographic zones
- `optimal_routing.py` - Generates distance-optimized routes

### Data Files (in /data/ folder)
- `tfp_clean_requests.csv` - All processed requests with size categories
- `complete_route_assignments.csv` - Full route details with GPS coordinates
- `truck_route_summary.csv` - Summary metrics per truck
- `booking_interface.json` - Calendar booking data
- `zone_schedule.csv` - Zone-based truck assignments

## API Endpoints Available

```python
from backend_api import api

# Dashboard metrics
api.get_dashboard_summary()

# All requests data  
api.get_all_requests()

# Truck assignments
api.get_truck_assignments()

# Optimized routes with GPS
api.get_optimal_routes()

# Calendar booking data
api.get_calendar_data()

# Book time slots
api.book_time_slot(request_id, date, time_slot, zone, size, address)
```

## Running the Backend

1. Process raw data: `python3 clean_data.py`
2. Generate routes: `python3 route_assignment.py`  
3. Create calendar: `python3 calendar_system.py`
4. Start API: `python3 backend_api.py`

## Features Implemented

Size categorization (small/medium/large)
Truck capacity constraints (3S, 2S+1M, 2M, 1L)
Zone-based grouping by zip codes
Calendar auto-population from requests
Optimal route generation with GPS coordinates
Combined delivery/pickup route assignment
API endpoints for dashboard integration

## Next Steps for Frontend Partner

Use the API endpoints and CSV files to build:
- Interactive dashboard showing scheduled activities
- Route maps with GPS coordinates
- Calendar booking interface
- Truck utilization metrics
- Next-in-line order recommendations
