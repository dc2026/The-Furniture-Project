# Import all the tools we need (like getting tools from a toolbox)
import pandas as pd           # Tool for working with spreadsheet data
import numpy as np            # Tool for math and number calculations
from datetime import datetime, timedelta  # Tools for working with dates and times
from sklearn.cluster import KMeans        # Tool for grouping similar things together
import pyswarms as ps         # Tool for finding the best route (like GPS optimization)
from geopy.distance import great_circle   # Tool for measuring distances between locations

# This is like creating a blueprint for our scheduling system
# Think of it as a recipe that contains all the instructions for scheduling deliveries
class TFPSchedulingSystem:
    # This is like setting up the basic rules when we create our scheduling system
    def __init__(self):  # __init__ means "initialize" - set up the starting conditions
        
        # Set the warehouse location (where trucks start and end their day)
        self.warehouse = [41.3, -96.0]  # Latitude and longitude of Omaha warehouse
        
        # Note: TFP packs trucks beforehand, so no capacity constraints needed
        
    # This function identifies if a request is a client delivery or donor pickup
    def identify_request_type(self, row):  # 'row' is one furniture request
        """Identify if this is a client delivery or donor pickup"""
        # Check the request type column to determine if it's delivery or pickup
        request_type = row.get("Is your client requesting", "")
        if pd.notna(request_type) and "pickup" in str(request_type).lower():
            return 'pickup'  # Donor pickup
        else:
            return 'delivery'  # Client delivery (default)
    
    def load_requests(self, csv_path):
        """Load and process furniture requests"""
        df = pd.read_csv(csv_path)
        requests = []
        
        for idx, row in df.iterrows():
            street_col = "Client's house number and street"
            city_col = "Client's City and State"
            zip_col = "Client's Zip Code"
            
            if pd.notna(row.get(street_col)) and pd.notna(row.get(city_col)):
                requests.append({
                    'id': idx + 1,
                    'client_name': row.get("Client's first name and last name", ""),
                    'address': f"{row[street_col]}, {row[city_col]}",
                    'zipcode': row.get(zip_col, ""),
                    'type': self.identify_request_type(row),
                    'phone': row.get("Client's contact phone number", ""),
                    'status': 'pending'
                })
        
        return pd.DataFrame(requests)
    
    def assign_zones(self, requests_df, n_zones=3):
        """Assign requests to geographic zones"""
        # Mock coordinates for demo (in production, use geocoding)
        np.random.seed(42)
        coords = np.random.uniform([41.2, -96.1], [41.4, -95.9], (len(requests_df), 2))
        
        kmeans = KMeans(n_clusters=n_zones, random_state=0)
        zones = kmeans.fit_predict(coords)
        
        requests_df['zone'] = zones
        requests_df['lat'] = coords[:, 0]
        requests_df['lon'] = coords[:, 1]
        
        return requests_df
    
    # Since TFP packs trucks beforehand, we don't need capacity checking
    # This function is simplified to just assign requests to zones
    def assign_to_truck(self, zone_requests, max_per_truck=5):
        """Assign requests to trucks - simplified since trucks are pre-packed"""
        # Simple assignment: up to 5 deliveries per truck (adjustable)
        # TFP can modify this number based on their actual truck capacity
        return len(zone_requests) <= max_per_truck
    
    def schedule_daily_routes(self, requests_df, date, max_per_truck=5):
        """Schedule requests for a specific date - simplified since trucks are pre-packed"""
        scheduled = []
        
        # Since TFP packs trucks beforehand, we just assign all requests in each zone to trucks
        for zone in requests_df['zone'].unique():
            zone_requests = requests_df[requests_df['zone'] == zone].copy()
            
            # Assign all requests in this zone to the zone's truck
            # TFP can adjust max_per_truck based on their actual capacity
            for _, request in zone_requests.iterrows():
                scheduled.append({
                    'date': date,
                    'zone': zone,
                    'truck_id': f"Truck_{zone + 1}",
                    'request_id': request['id'],
                    'client_name': request['client_name'],
                    'address': request['address'],
                    'type': request['type'],  # delivery or pickup
                    'phone': request['phone'],
                    'lat': request.get('lat', 41.25),
                    'lon': request.get('lon', -96.0)
                })
        
        return pd.DataFrame(scheduled)
    
    def optimize_route(self, scheduled_df, zone):
        """Optimize route following TFP's workflow: Warehouse → Client Deliveries → Donor Pickups → Warehouse"""
        zone_requests = scheduled_df[scheduled_df['zone'] == zone]
        
        if len(zone_requests) == 0:
            return [], 0
        
        # Separate client deliveries and donor pickups
        deliveries = zone_requests[zone_requests['type'] == 'delivery']
        pickups = zone_requests[zone_requests['type'] == 'pickup']
        
        # Build the route following TFP's workflow
        route = []
        total_distance = 0
        
        # Start at warehouse
        current_location = self.warehouse
        route.append({
            'stop_type': 'warehouse_start',
            'address': 'TFP Warehouse - Start',
            'coordinates': self.warehouse,
            'type': 'warehouse'
        })
        
        # PHASE 1: Client Deliveries (optimize order within deliveries)
        if len(deliveries) > 0:
            delivery_coords = []
            for _, delivery in deliveries.iterrows():
                coords = [delivery.get('lat', 41.25), delivery.get('lon', -96.0)]
                delivery_coords.append(coords)
                
            # Optimize delivery order using nearest neighbor
            optimized_deliveries = self.nearest_neighbor_optimize(delivery_coords, current_location)
            
            # Add optimized deliveries to route
            for i, delivery_idx in enumerate(optimized_deliveries):
                delivery = deliveries.iloc[delivery_idx]
                coords = [delivery.get('lat', 41.25), delivery.get('lon', -96.0)]
                
                # Calculate distance from current location
                distance = great_circle(current_location, coords).miles
                total_distance += distance
                current_location = coords
                
                route.append({
                    'stop_type': 'client_delivery',
                    'address': delivery['address'],
                    'coordinates': coords,
                    'type': 'delivery',
                    'client_name': delivery['client_name'],
                    'phone': delivery['phone']
                })
        
        # PHASE 2: Donor Pickups (optimize order within pickups)
        if len(pickups) > 0:
            pickup_coords = []
            for _, pickup in pickups.iterrows():
                coords = [pickup.get('lat', 41.25), pickup.get('lon', -96.0)]
                pickup_coords.append(coords)
                
            # Optimize pickup order using nearest neighbor
            optimized_pickups = self.nearest_neighbor_optimize(pickup_coords, current_location)
            
            # Add optimized pickups to route
            for i, pickup_idx in enumerate(optimized_pickups):
                pickup = pickups.iloc[pickup_idx]
                coords = [pickup.get('lat', 41.25), pickup.get('lon', -96.0)]
                
                # Calculate distance from current location
                distance = great_circle(current_location, coords).miles
                total_distance += distance
                current_location = coords
                
                route.append({
                    'stop_type': 'donor_pickup',
                    'address': pickup['address'],
                    'coordinates': coords,
                    'type': 'pickup',
                    'client_name': pickup['client_name'],
                    'phone': pickup['phone']
                })
        
        # End at warehouse
        distance = great_circle(current_location, self.warehouse).miles
        total_distance += distance
        
        route.append({
            'stop_type': 'warehouse_end',
            'address': 'TFP Warehouse - Return',
            'coordinates': self.warehouse,
            'type': 'warehouse'
        })
        
        return route, total_distance
    
    def nearest_neighbor_optimize(self, coords_list, start_location):
        """Simple nearest neighbor optimization for a list of coordinates"""
        if len(coords_list) <= 1:
            return list(range(len(coords_list)))
        
        unvisited = list(range(len(coords_list)))
        route_order = []
        current_pos = start_location
        
        while unvisited:
            # Find nearest unvisited location
            nearest_idx = min(unvisited, key=lambda i: great_circle(current_pos, coords_list[i]).miles)
            route_order.append(nearest_idx)
            unvisited.remove(nearest_idx)
            current_pos = coords_list[nearest_idx]
        
        return route_order

# This section runs when someone executes this file directly
# Think of it as a "test drive" of our scheduling system
if __name__ == "__main__":  # This means "if someone runs this file directly"
    
    # Create our scheduling system (like starting up a computer program)
    system = TFPSchedulingSystem()
    
    # STEP 1: Load all the furniture requests from the spreadsheet
    requests = system.load_requests('furniture_project_requests - Request Assistance Form .csv')
    print(f"Loaded {len(requests)} requests")  # Show how many requests we found
    
    # STEP 2: Group the requests into geographic zones (like dividing the city into neighborhoods)
    requests = system.assign_zones(requests)
    
    # STEP 3: Create a schedule for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)  # Get tomorrow's date
    # Create the actual delivery schedule
    schedule = system.schedule_daily_routes(requests, tomorrow.strftime('%Y-%m-%d'))
    
    # Show how many deliveries we scheduled
    print(f"\nScheduled {len(schedule)} deliveries for {tomorrow.strftime('%Y-%m-%d')}")
    
    # STEP 4: Show the schedule organized by truck/zone
    for zone in schedule['zone'].unique():  # Go through each zone
        zone_schedule = schedule[schedule['zone'] == zone]  # Get deliveries for this zone
        print(f"\nZone {zone} - Truck_{zone + 1}:")  # Show which truck handles this zone
        
        # Show optimized route for this truck
        route, distance = system.optimize_route(schedule, zone)
        print(f"  Optimized route: {distance:.1f} miles")
        
        # List each stop in optimized order
        for i, stop in enumerate(route):
            if stop['type'] in ['delivery', 'pickup']:
                stop_type = "📦 Delivery" if stop['type'] == 'delivery' else "🏠 Pickup"
                print(f"  {i}. {stop_type}: {stop.get('client_name', 'Unknown')} - {stop['address']}")
    
    # STEP 5: Save the schedule to a file (like saving a document)
    schedule.to_csv('daily_schedule.csv', index=False)  # Save as a spreadsheet file
    print(f"\nSchedule saved to daily_schedule.csv")  # Confirm it was saved