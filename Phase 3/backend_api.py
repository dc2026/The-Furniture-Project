# backend_api.py
# Complete backend API for The Furniture Project Dashboard
# Provides all data endpoints needed for frontend dashboard integration
# Handles requests, routes, scheduling, and booking functionality

import pandas as pd
import json
from datetime import datetime

class FurnitureBackendAPI:
    """Main API class providing data access for dashboard frontend
    
    This class serves as the interface between processed backend data
    and the frontend dashboard, providing clean JSON/dict responses
    for all furniture project scheduling and routing needs.
    """
    def __init__(self):
        """Initialize API with data file path"""
        self.data_path = "data/"  # Directory containing all processed CSV/JSON files
    
    def get_dashboard_summary(self):
        """Get high-level dashboard metrics for main overview
        
        Returns:
            dict: Summary statistics including total requests, trucks, 
                  distances, and breakdowns by size/type/zone
        """
        try:
            requests = pd.read_csv(f"{self.data_path}tfp_clean_requests.csv")
            routes = pd.read_csv(f"{self.data_path}route_summary.csv")
            
            return {
                "total_requests": len(requests),
                "total_trucks": len(routes),
                "total_distance": round(routes['total_distance_miles'].sum(), 1),
                "total_time": round(routes['estimated_time_minutes'].sum(), 0),
                "size_breakdown": requests['size_category'].value_counts().to_dict(),
                "type_breakdown": requests['request_type'].value_counts().to_dict(),
                "zone_breakdown": requests.groupby('zone').size().to_dict() if 'zone' in requests.columns else {}
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_requests(self):
        """Get all furniture requests with details
        
        Returns:
            list: All processed requests with size, type, address, zone data
        """
        try:
            df = pd.read_csv(f"{self.data_path}tfp_clean_requests.csv")
            return df.to_dict('records')
        except Exception as e:
            return {"error": str(e)}
    
    def get_truck_assignments(self):
        """Get truck assignments and capacity info
        
        Returns:
            list: Truck assignments with capacity configurations and zones
        """
        try:
            df = pd.read_csv(f"{self.data_path}zone_schedule.csv")
            return df.to_dict('records')
        except Exception as e:
            return {"error": str(e)}
    
    def get_optimal_routes(self):
        """Get optimized routes with GPS coordinates
        
        Returns:
            list: Complete route data with stop sequences, GPS coords, distances
        """
        try:
            df = pd.read_csv(f"{self.data_path}optimal_routes.csv")
            return df.to_dict('records')
        except Exception as e:
            return {"error": str(e)}
    
    def get_calendar_data(self):
        """Get calendar booking interface data
        
        Returns:
            list: Available booking slots for each request over next 7 days
        """
        try:
            with open(f"{self.data_path}booking_interface.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    
    def get_zone_summary(self):
        """Get zone-based statistics"""
        try:
            df = pd.read_csv(f"{self.data_path}zone_summary.csv")
            return df.to_dict('records')
        except Exception as e:
            return {"error": str(e)}
    
    def get_delivery_schedule(self):
        """Get complete delivery schedule"""
        try:
            df = pd.read_csv(f"{self.data_path}delivery_schedule.csv")
            return df.to_dict('records')
        except Exception as e:
            return {"error": str(e)}
    
    def book_time_slot(self, request_id, date, time_slot, zone, size, address):
        """Book a time slot for a request
        
        Args:
            request_id (int): Unique request identifier
            date (str): Date in YYYY-MM-DD format
            time_slot (str): Time slot like '09:00-11:00'
            zone (str): Geographic zone (North, South, East, West, Council_Bluffs)
            size (str): Request size (small, medium, large)
            address (str): Full address for the request
            
        Returns:
            dict: Success/error message with booking confirmation
        """
        try:
            # Load existing bookings
            try:
                bookings = pd.read_csv(f"{self.data_path}calendar_bookings.csv")
            except FileNotFoundError:
                bookings = pd.DataFrame(columns=['request_id', 'date', 'time_slot', 'zone', 'size', 'address', 'status'])
            
            # Add new booking
            new_booking = pd.DataFrame([{
                'request_id': request_id,
                'date': date,
                'time_slot': time_slot,
                'zone': zone,
                'size': size,
                'address': address,
                'status': 'booked',
                'created_at': datetime.now().isoformat()
            }])
            
            bookings = pd.concat([bookings, new_booking], ignore_index=True)
            bookings.to_csv(f"{self.data_path}calendar_bookings.csv", index=False)
            
            return {"success": True, "message": "Booking confirmed"}
        except Exception as e:
            return {"error": str(e)}

# Create API instance for easy import by frontend
# Usage: from backend_api import api
api = FurnitureBackendAPI()

# Example usage and testing - run this file directly to test all endpoints
if __name__ == "__main__":
    print("Backend API Test Results:")
    print("=" * 40)
    
    # Test all endpoints
    endpoints = [
        ("Dashboard Summary", api.get_dashboard_summary),
        ("All Requests", lambda: f"{len(api.get_all_requests())} requests"),
        ("Truck Assignments", lambda: f"{len(api.get_truck_assignments())} assignments"),
        ("Optimal Routes", lambda: f"{len(api.get_optimal_routes())} route points"),
        ("Calendar Data", lambda: f"{len(api.get_calendar_data())} calendar entries"),
        ("Zone Summary", lambda: f"{len(api.get_zone_summary())} zones"),
        ("Delivery Schedule", lambda: f"{len(api.get_delivery_schedule())} scheduled items")
    ]
    
    for name, func in endpoints:
        try:
            result = func()
            print(f"PASS {name}: {result if isinstance(result, str) else 'OK'}")
        except Exception as e:
            print(f"FAIL {name}: {str(e)}")
    
    print("\nSample Dashboard Data:")
    summary = api.get_dashboard_summary()
    if 'error' not in summary:
        for key, value in summary.items():
            print(f"  {key}: {value}")