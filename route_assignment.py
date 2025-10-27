# route_assignment.py
# Assign complete routes to trucks for deliveries and pickups
# This is the core optimization engine that creates efficient truck routes
# combining pickups (from donors) and deliveries (to clients) with capacity constraints

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt

class RouteAssigner:
    """Main route optimization class for furniture delivery/pickup scheduling
    
    This class handles:
    - Truck capacity constraints (3 small, 2 medium, or 1 large)
    - Geographic optimization using GPS coordinates
    - Mixed pickup/delivery route planning
    - Distance and time calculations
    """
    def __init__(self):
        """Initialize route assigner with depot location and truck configurations"""
        self.depot = (41.2565, -95.9345)  # Omaha center - all routes start/end here
        
        # Available truck capacity configurations
        # Each truck can carry ONE of these combinations:
        self.truck_configs = [
            {"small": 3, "medium": 0, "large": 0},  # 3 small items
            {"small": 2, "medium": 1, "large": 0},  # 2 small + 1 medium
            {"small": 0, "medium": 2, "large": 0},  # 2 medium items
            {"small": 0, "medium": 0, "large": 1}   # 1 large item
        ]
    
    def load_data(self):
        """Load request data"""
        try:
            self.df = pd.read_csv("data/tfp_clean_requests.csv")
            return True
        except FileNotFoundError:
            print("Run clean_data.py first")
            return False
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS points using Haversine formula
        
        Args:
            lat1, lon1: Latitude/longitude of first point
            lat2, lon2: Latitude/longitude of second point
            
        Returns:
            float: Distance in miles
        """
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return 2 * asin(sqrt(a)) * 3959
    
    def get_coordinates(self, address):
        """Get GPS coordinates for address using zip code lookup
        
        Args:
            address (str): Full address string
            
        Returns:
            tuple: (latitude, longitude) coordinates
        """
        zip_coords = {
            '68104': (41.3114, -95.9208), '68111': (41.3456, -95.9017),
            '68134': (41.2072, -96.1003), '68106': (41.2033, -95.9778),
            '68127': (41.1544, -96.0142), '68130': (40.8136, -96.6917),
            '68137': (41.1836, -95.8975), '68108': (41.2203, -95.8608),
            '68114': (41.2203, -95.8608), '68124': (41.2500, -96.0500),
            '68132': (41.2203, -95.8608), '68131': (41.2978, -96.0419),
            '51501': (41.2619, -95.8608)
        }
        
        # Extract zip from address
        parts = str(address).split()
        for part in parts:
            clean_zip = part.replace(',', '')
            if clean_zip in zip_coords:
                return zip_coords[clean_zip]
        return self.depot
    
    def pack_truck(self, requests):
        """Pack requests into truck using capacity constraints
        
        Tries each truck configuration to find the best fit.
        Prioritizes pickups first (collect items), then deliveries.
        
        Args:
            requests (list): Available requests to assign
            
        Returns:
            tuple: (truck_load, config) - assigned items and truck configuration
        """
        for config in self.truck_configs:
            truck_load = []
            capacity = config.copy()
            
            # Separate by type and size
            pickups = [r for r in requests if r['type'] == 'pickup']
            deliveries = [r for r in requests if r['type'] == 'delivery']
            
            # Fill with pickups first (collect items)
            for size in ['large', 'medium', 'small']:
                available_pickups = [p for p in pickups if p['size'] == size]
                take_count = min(capacity[size], len(available_pickups))
                
                for i in range(take_count):
                    if available_pickups:
                        item = available_pickups.pop(0)
                        truck_load.append(item)
                        capacity[size] -= 1
                        pickups.remove(item)
            
            # Fill remaining capacity with deliveries
            for size in ['large', 'medium', 'small']:
                available_deliveries = [d for d in deliveries if d['size'] == size]
                take_count = min(capacity[size], len(available_deliveries))
                
                for i in range(take_count):
                    if available_deliveries:
                        item = available_deliveries.pop(0)
                        truck_load.append(item)
                        capacity[size] -= 1
                        deliveries.remove(item)
            
            if truck_load:
                return truck_load, config
        
        return [], {}
    
    def optimize_route_order(self, truck_load):
        """Optimize the order of stops for a truck
        
        Creates logical route: Depot -> Pickups -> Deliveries -> Depot
        Uses nearest neighbor algorithm to minimize travel distance.
        
        Args:
            truck_load (list): Items assigned to this truck
            
        Returns:
            list: Optimized sequence of stops with coordinates
        """
        if not truck_load:
            return []
        
        # Separate pickups and deliveries
        pickups = [item for item in truck_load if item['type'] == 'pickup']
        deliveries = [item for item in truck_load if item['type'] == 'delivery']
        
        # Get coordinates for all stops
        for item in truck_load:
            item['coordinates'] = self.get_coordinates(item['address'])
        
        # Optimize pickup order (nearest neighbor)
        optimized_pickups = self.nearest_neighbor_route(pickups)
        
        # Optimize delivery order
        optimized_deliveries = self.nearest_neighbor_route(deliveries)
        
        # Route: Depot -> Pickups -> Deliveries -> Depot
        route = []
        
        # Add depot start
        route.append({
            'stop_type': 'depot_start',
            'address': 'Depot - Start',
            'coordinates': self.depot,
            'type': 'depot',
            'size': 'depot'
        })
        
        # Add pickups
        route.extend(optimized_pickups)
        
        # Add deliveries
        route.extend(optimized_deliveries)
        
        # Add depot end
        route.append({
            'stop_type': 'depot_end',
            'address': 'Depot - Return',
            'coordinates': self.depot,
            'type': 'depot',
            'size': 'depot'
        })
        
        return route
    
    def nearest_neighbor_route(self, stops):
        """Optimize stops using nearest neighbor algorithm
        
        Greedy algorithm that always goes to the closest unvisited stop.
        Simple but effective for small route optimization.
        
        Args:
            stops (list): List of stops to optimize
            
        Returns:
            list: Stops in optimized order
        """
        if len(stops) <= 1:
            return stops
        
        optimized = []
        remaining = stops.copy()
        current_pos = self.depot
        
        while remaining:
            # Find nearest stop
            nearest = min(remaining, key=lambda x: self.haversine_distance(
                current_pos[0], current_pos[1],
                x['coordinates'][0], x['coordinates'][1]
            ))
            
            optimized.append(nearest)
            remaining.remove(nearest)
            current_pos = nearest['coordinates']
        
        return optimized
    
    def calculate_route_metrics(self, route):
        """Calculate total distance and time for complete route
        
        Includes travel time between stops plus service time at each location.
        
        Args:
            route (list): Complete route with all stops
            
        Returns:
            tuple: (total_distance_miles, total_time_minutes)
        """
        total_distance = 0
        total_time = 0
        
        for i in range(len(route) - 1):
            current = route[i]['coordinates']
            next_stop = route[i + 1]['coordinates']
            
            distance = self.haversine_distance(
                current[0], current[1],
                next_stop[0], next_stop[1]
            )
            
            total_distance += distance
            
            # Add service time
            if route[i + 1]['type'] == 'pickup':
                total_time += 30  # 30 min for pickup
            elif route[i + 1]['type'] == 'delivery':
                total_time += 20  # 20 min for delivery
            
            # Add travel time (2.5 min per mile)
            total_time += distance * 2.5
        
        return total_distance, total_time
    
    def assign_all_routes(self):
        """Assign optimized routes to all trucks
        
        Main orchestration function that:
        1. Loads and processes request data
        2. Packs trucks with capacity constraints
        3. Optimizes route order for each truck
        4. Calculates performance metrics
        
        Returns:
            list: Complete truck assignments with routes and metrics
        """
        if not self.load_data():
            return None
        
        # Prepare request data
        requests = []
        for _, row in self.df.iterrows():
            requests.append({
                'id': row.name,
                'address': row['Full Address'],
                'size': row['size_category'],
                'type': row['request_type'] if row['request_type'] in ['pickup', 'delivery'] else 'delivery'
            })
        
        trucks = []
        truck_id = 1
        
        while requests:
            # Pack truck
            truck_load, config = self.pack_truck(requests)
            
            if not truck_load:
                break
            
            # Optimize route order
            optimized_route = self.optimize_route_order(truck_load)
            
            # Calculate metrics
            distance, time = self.calculate_route_metrics(optimized_route)
            
            trucks.append({
                'truck_id': f"ROUTE_{truck_id}",
                'config': f"{config['small']}S+{config['medium']}M+{config['large']}L",
                'route': optimized_route,
                'total_distance': round(distance, 2),
                'total_time': round(time, 0),
                'pickup_count': len([s for s in optimized_route if s.get('type') == 'pickup']),
                'delivery_count': len([s for s in optimized_route if s.get('type') == 'delivery'])
            })
            
            truck_id += 1
            
            # Remove assigned requests
            for item in truck_load:
                requests = [r for r in requests if r['id'] != item['id']]
        
        return trucks
    
    def save_route_assignments(self, trucks):
        """Save complete route assignments to CSV files
        
        Creates two output files:
        - complete_route_assignments.csv: Detailed route data
        - truck_route_summary.csv: Summary metrics per truck
        
        Args:
            trucks (list): All truck assignments with routes
        """
        route_data = []
        
        for truck in trucks:
            for i, stop in enumerate(truck['route']):
                route_data.append({
                    'truck_id': truck['truck_id'],
                    'config': truck['config'],
                    'stop_sequence': i,
                    'stop_type': stop.get('stop_type', stop['type']),
                    'address': stop['address'],
                    'latitude': stop['coordinates'][0],
                    'longitude': stop['coordinates'][1],
                    'size': stop['size'],
                    'total_distance': truck['total_distance'],
                    'total_time': truck['total_time']
                })
        
        pd.DataFrame(route_data).to_csv("data/complete_route_assignments.csv", index=False)
        
        # Create truck summary
        summary_data = []
        for truck in trucks:
            summary_data.append({
                'truck_id': truck['truck_id'],
                'config': truck['config'],
                'total_stops': len(truck['route']) - 2,  # Exclude depot start/end
                'pickups': truck['pickup_count'],
                'deliveries': truck['delivery_count'],
                'distance_miles': truck['total_distance'],
                'time_minutes': truck['total_time']
            })
        
        pd.DataFrame(summary_data).to_csv("data/truck_route_summary.csv", index=False)
        
        print(f"Complete route assignments saved to: data/complete_route_assignments.csv")
        print(f"Truck summary saved to: data/truck_route_summary.csv")

# Run the route assigner - execute this file to generate optimized routes
if __name__ == "__main__":
    assigner = RouteAssigner()
    trucks = assigner.assign_all_routes()
    
    if trucks:
        assigner.save_route_assignments(trucks)
        
        print(f"\nRoute Assignment Summary:")
        print(f"Total trucks: {len(trucks)}")
        
        total_distance = sum(t['total_distance'] for t in trucks)
        total_time = sum(t['total_time'] for t in trucks)
        total_pickups = sum(t['pickup_count'] for t in trucks)
        total_deliveries = sum(t['delivery_count'] for t in trucks)
        
        print(f"Total distance: {total_distance:.1f} miles")
        print(f"Total time: {total_time:.0f} minutes")
        print(f"Total pickups: {total_pickups}")
        print(f"Total deliveries: {total_deliveries}")
        
        print(f"\nSample routes:")
        for truck in trucks[:3]:
            print(f"{truck['truck_id']}: {truck['pickup_count']} pickups, {truck['delivery_count']} deliveries")
    else:
        print("No routes assigned. Check data files.")