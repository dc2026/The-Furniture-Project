# route_assignment.py
# 🗺️ GPS-POWERED ROUTE OPTIMIZATION FOR THE FURNITURE PROJECT
# 
# WHAT THIS DOES:
# Takes scattered furniture requests around Omaha and creates the most efficient
# truck routes that minimize driving time and respect truck capacity limits.
# Think of it as Google Maps for furniture delivery trucks!
#
# HOW IT WORKS:
# 1. Loads furniture requests (pickups from donors, deliveries to clients)
# 2. Packs trucks like Tetris (3 small OR 2 medium OR 1 large per truck)
# 3. Creates GPS routes: Warehouse → Pickups → Deliveries → Warehouse
# 4. Uses "nearest neighbor" algorithm to minimize driving distance
# 5. Calculates total miles and time for each truck route

# Import the tools we need (like getting tools from a toolbox)
import pandas as pd          # Tool for working with spreadsheet data
import numpy as np           # Tool for math calculations
from math import radians, cos, sin, asin, sqrt  # Tools for GPS distance calculations

class RouteAssigner:
    """🚚 SMART TRUCK ROUTE OPTIMIZER
    
    This is like having a GPS system that knows about truck capacity limits.
    It creates the most efficient routes for furniture delivery trucks.
    
    What it handles:
    - Truck capacity rules (3 small OR 2 medium OR 1 large items)
    - GPS coordinates and distance calculations
    - Mixed routes (pickups from donors + deliveries to clients)
    - Time estimates including driving and loading/unloading
    """
    def __init__(self):
        """🏭 SET UP THE ROUTE OPTIMIZER
        
        This is like setting up a GPS system with TFP's warehouse location
        and truck capacity rules.
        """
        # 📍 TFP Warehouse location (all trucks start and end here)
        # These are GPS coordinates: (latitude, longitude) for Omaha center
        self.depot = (41.2565, -95.9345)
        
        # 📦 TRUCK CAPACITY RULES (like Tetris combinations)
        # Each truck can carry ONE of these combinations - no mixing!
        # Think of it like different sized moving trucks
        self.truck_configs = [
            {"small": 3, "medium": 0, "large": 0},  # Small truck: 3 small items (lamps, chairs, etc.)
            {"small": 2, "medium": 1, "large": 0},  # Mixed load: 2 small + 1 medium (table, dresser)
            {"small": 0, "medium": 2, "large": 0},  # Medium truck: 2 medium items
            {"small": 0, "medium": 0, "large": 1}   # Large truck: 1 large item (sofa, bed, etc.)
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
        """📏 CALCULATE DRIVING DISTANCE BETWEEN TWO GPS POINTS
        
        This is like asking "How far is it from Point A to Point B?"
        Uses the Haversine formula which accounts for Earth's curvature.
        
        Think of it like: If you put two pins on Google Maps, this calculates
        the straight-line distance between them.
        
        Args:
            lat1, lon1: GPS coordinates of first location (like 123 Main St)
            lat2, lon2: GPS coordinates of second location (like 456 Oak Ave)
            
        Returns:
            float: Distance in miles (like "12.5 miles")
        """
        # Convert GPS coordinates from degrees to radians (math requirement)
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Calculate the differences in coordinates
        dlat = lat2 - lat1  # How far north/south
        dlon = lon2 - lon1  # How far east/west
        
        # Haversine formula - complex math to handle Earth's curvature
        # This accounts for the fact that Earth is round, not flat
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        
        # Convert to miles (3959 is Earth's radius in miles)
        return 2 * asin(sqrt(a)) * 3959
    
    def get_coordinates(self, address):
        """📍 CONVERT ADDRESS TO GPS COORDINATES
        
        This is like looking up an address on Google Maps to get its exact location.
        We use zip codes to find GPS coordinates (latitude, longitude).
        
        Example: "123 Main St, Omaha NE 68104" → (41.3114, -95.9208)
        
        Args:
            address (str): Full address like "123 Main St, Omaha NE 68104"
            
        Returns:
            tuple: GPS coordinates like (41.3114, -95.9208)
        """
        # 🗺️ ZIP CODE TO GPS COORDINATE LOOKUP TABLE
        # This is like a phone book that converts zip codes to map locations
        # Each zip code has its center point's GPS coordinates
        zip_coords = {
            '68104': (41.3114, -95.9208),  # North Omaha
            '68111': (41.3456, -95.9017),  # Northeast Omaha
            '68134': (41.2072, -96.1003),  # West Omaha
            '68106': (41.2033, -95.9778),  # South Omaha
            '68127': (41.1544, -96.0142),  # Southwest Omaha
            '68130': (40.8136, -96.6917),  # Lincoln area
            '68137': (41.1836, -95.8975),  # Bellevue
            '68108': (41.2203, -95.8608),  # Central Omaha
            '68114': (41.2203, -95.8608),  # Benson
            '68124': (41.2500, -96.0500),  # West Omaha
            '68132': (41.2203, -95.8608),  # Northwest Omaha
            '68131': (41.2978, -96.0419),  # Midtown
            '51501': (41.2619, -95.8608)   # Council Bluffs, IA
        }
        
        # 🔍 EXTRACT ZIP CODE FROM ADDRESS
        # Split address into words and look for zip code
        parts = str(address).split()  # ["123", "Main", "St,", "Omaha", "NE", "68104"]
        
        for part in parts:
            clean_zip = part.replace(',', '')  # Remove commas: "68104," → "68104"
            if clean_zip in zip_coords:        # Check if this zip code is in our lookup table
                return zip_coords[clean_zip]   # Return the GPS coordinates
        
        # If no zip code found, default to warehouse location
        return self.depot
    
    def pack_truck(self, requests):
        """📦 SMART TRUCK PACKING (LIKE TETRIS FOR FURNITURE)
        
        This figures out the best way to pack furniture requests into a truck.
        It's like playing Tetris - certain combinations fit, others don't.
        
        STRATEGY:
        1. Try each truck configuration (3 small, 2 medium, 1 large, etc.)
        2. Fill with PICKUPS first (collect furniture from donors)
        3. Fill remaining space with DELIVERIES (deliver to clients)
        4. Choose the configuration that fits the most items
        
        WHY PICKUPS FIRST?
        You can't deliver furniture you haven't picked up yet!
        
        Args:
            requests (list): All available furniture requests to assign
            
        Returns:
            tuple: (truck_load, config) - what goes on this truck and which capacity rule
        """
        # 🎯 TRY EACH TRUCK CONFIGURATION
        # Like trying different sized moving trucks to see which fits best
        for config in self.truck_configs:
            truck_load = []           # What we'll put on this truck
            capacity = config.copy()  # How much space we have left
            
            # 📋 SEPARATE REQUESTS BY TYPE
            # Pickups = collecting furniture from donors
            # Deliveries = taking furniture to clients who need it
            pickups = [r for r in requests if r['type'] == 'pickup']
            deliveries = [r for r in requests if r['type'] == 'delivery']
            
            # 🚚 STEP 1: FILL WITH PICKUPS FIRST
            # We need to collect furniture before we can deliver it!
            # Try large items first (they take most space), then medium, then small
            for size in ['large', 'medium', 'small']:
                # Find all pickups of this size that are available
                available_pickups = [p for p in pickups if p['size'] == size]
                
                # Take as many as we can fit (limited by truck capacity)
                take_count = min(capacity[size], len(available_pickups))
                
                # Add them to the truck
                for i in range(take_count):
                    if available_pickups:
                        item = available_pickups.pop(0)  # Take the first available item
                        truck_load.append(item)          # Put it on the truck
                        capacity[size] -= 1              # Reduce available space
                        pickups.remove(item)             # Remove from available list
            
            # 🏠 STEP 2: FILL REMAINING SPACE WITH DELIVERIES
            # Use whatever truck space is left for client deliveries
            for size in ['large', 'medium', 'small']:
                # Find all deliveries of this size that are available
                available_deliveries = [d for d in deliveries if d['size'] == size]
                
                # Take as many as we can fit in remaining space
                take_count = min(capacity[size], len(available_deliveries))
                
                # Add them to the truck
                for i in range(take_count):
                    if available_deliveries:
                        item = available_deliveries.pop(0)  # Take the first available item
                        truck_load.append(item)             # Put it on the truck
                        capacity[size] -= 1                 # Reduce available space
                        deliveries.remove(item)             # Remove from available list
            
            # ✅ If we managed to fit anything on this truck, use this configuration
            if truck_load:
                return truck_load, config
        
        # ❌ If no configuration worked, return empty truck
        return [], {}
    
    def optimize_route_order(self, truck_load):
        """🗺️ CREATE THE MOST EFFICIENT DRIVING ROUTE
        
        This is like asking Google Maps for the best route, but for furniture trucks.
        Creates a logical route that minimizes driving time and distance.
        
        ROUTE LOGIC:
        Warehouse → All Pickups → All Deliveries → Warehouse
        
        WHY THIS ORDER?
        - Start at warehouse (where trucks are parked)
        - Do all pickups first (collect furniture from donors)
        - Then do all deliveries (deliver to clients)
        - Return to warehouse (end of day)
        
        OPTIMIZATION:
        Uses "nearest neighbor" algorithm - always go to the closest next stop.
        
        Args:
            truck_load (list): All the furniture requests assigned to this truck
            
        Returns:
            list: Complete route with GPS coordinates for each stop
        """
        # 🚫 If truck is empty, no route needed
        if not truck_load:
            return []
        
        # 📋 SEPARATE PICKUPS AND DELIVERIES
        # Pickups = collecting furniture from donors
        # Deliveries = taking furniture to clients
        pickups = [item for item in truck_load if item['type'] == 'pickup']
        deliveries = [item for item in truck_load if item['type'] == 'delivery']
        
        # 📍 GET GPS COORDINATES FOR ALL STOPS
        # Convert addresses like "123 Main St" to GPS coordinates like (41.31, -95.92)
        for item in truck_load:
            item['coordinates'] = self.get_coordinates(item['address'])
        
        # 🎯 OPTIMIZE THE ORDER OF PICKUPS
        # Find the shortest path to visit all pickup locations
        optimized_pickups = self.nearest_neighbor_route(pickups)
        
        # 🎯 OPTIMIZE THE ORDER OF DELIVERIES
        # Find the shortest path to visit all delivery locations
        optimized_deliveries = self.nearest_neighbor_route(deliveries)
        
        # 🛣️ BUILD THE COMPLETE ROUTE
        # Warehouse → Pickups → Deliveries → Warehouse
        route = []
        
        # 🏭 START: Warehouse (beginning of day)
        route.append({
            'stop_type': 'depot_start',
            'address': 'TFP Warehouse - Start',
            'coordinates': self.depot,
            'type': 'depot',
            'size': 'depot'
        })
        
        # 📦 ADD ALL PICKUPS (collect furniture from donors)
        route.extend(optimized_pickups)
        
        # 🏠 ADD ALL DELIVERIES (deliver furniture to clients)
        route.extend(optimized_deliveries)
        
        # 🏭 END: Return to warehouse (end of day)
        route.append({
            'stop_type': 'depot_end',
            'address': 'TFP Warehouse - Return',
            'coordinates': self.depot,
            'type': 'depot',
            'size': 'depot'
        })
        
        return route
    
    def nearest_neighbor_route(self, stops):
        """🧭 FIND THE SHORTEST PATH THROUGH ALL STOPS
        
        This uses the "Nearest Neighbor" algorithm - a simple but effective way
        to minimize driving distance. Think of it like this:
        
        "From where I am now, which stop is closest? Go there next."
        "From that stop, which remaining stop is closest? Go there next."
        "Repeat until all stops are visited."
        
        It's like connecting dots on a map by always choosing the shortest line.
        
        EXAMPLE:
        Current location: Warehouse
        Remaining stops: [A, B, C]
        - A is 5 miles away, B is 12 miles, C is 8 miles → Go to A
        - From A: B is 7 miles away, C is 3 miles → Go to C  
        - From C: Only B left → Go to B
        - Final route: Warehouse → A → C → B
        
        Args:
            stops (list): List of pickup or delivery stops to optimize
            
        Returns:
            list: Stops arranged in the order that minimizes driving distance
        """
        # 🚫 If 1 or fewer stops, no optimization needed
        if len(stops) <= 1:
            return stops
        
        optimized = []                # The optimized route we're building
        remaining = stops.copy()      # Stops we haven't visited yet
        current_pos = self.depot      # Start at the warehouse
        
        # 🔄 KEEP GOING UNTIL ALL STOPS ARE VISITED
        while remaining:
            # 🎯 FIND THE CLOSEST UNVISITED STOP
            # Calculate distance from current location to each remaining stop
            # Choose the one with the shortest distance
            nearest = min(remaining, key=lambda x: self.haversine_distance(
                current_pos[0], current_pos[1],        # Where we are now
                x['coordinates'][0], x['coordinates'][1]  # Where this stop is
            ))
            
            # ✅ ADD THIS STOP TO OUR ROUTE
            optimized.append(nearest)     # Add to our optimized route
            remaining.remove(nearest)     # Remove from unvisited list
            current_pos = nearest['coordinates']  # Update our current location
        
        return optimized
    
    def calculate_route_metrics(self, route):
        """⏱️ CALCULATE TOTAL MILES AND TIME FOR THE COMPLETE ROUTE
        
        This figures out how long the truck route will take and how far it will drive.
        Includes both driving time AND time spent loading/unloading furniture.
        
        TIME BREAKDOWN:
        - Driving time: 2.5 minutes per mile (city driving with traffic)
        - Pickup time: 30 minutes (load furniture from donor)
        - Delivery time: 20 minutes (unload furniture to client)
        
        EXAMPLE:
        Route: Warehouse → Pickup (5 miles) → Delivery (8 miles) → Warehouse (6 miles)
        - Driving: (5+8+6) × 2.5 = 47.5 minutes
        - Pickup: 30 minutes
        - Delivery: 20 minutes
        - Total: 97.5 minutes, 19 miles
        
        Args:
            route (list): Complete route with all stops and GPS coordinates
            
        Returns:
            tuple: (total_distance_miles, total_time_minutes)
        """
        total_distance = 0  # Total miles driven
        total_time = 0      # Total time including driving + service
        
        # 🔄 GO THROUGH EACH SEGMENT OF THE ROUTE
        # Calculate distance and time from each stop to the next
        for i in range(len(route) - 1):
            current = route[i]['coordinates']      # Where we are now
            next_stop = route[i + 1]['coordinates']  # Where we're going next
            
            # 📏 CALCULATE DRIVING DISTANCE
            distance = self.haversine_distance(
                current[0], current[1],      # Current GPS coordinates
                next_stop[0], next_stop[1]   # Next stop GPS coordinates
            )
            
            total_distance += distance  # Add to total miles
            
            # ⏰ ADD SERVICE TIME (time spent at each stop)
            if route[i + 1]['type'] == 'pickup':
                total_time += 30  # 30 minutes to load furniture from donor
            elif route[i + 1]['type'] == 'delivery':
                total_time += 20  # 20 minutes to unload furniture to client
            # Note: No service time added for depot (warehouse) stops
            
            # 🚗 ADD DRIVING TIME (2.5 minutes per mile)
            # This accounts for city driving with traffic lights, turns, etc.
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