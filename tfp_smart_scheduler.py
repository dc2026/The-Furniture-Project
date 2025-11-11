# TFP Smart Scheduler - Matches TFP's Actual Process
# 1. Clients select 3 preferred time slots
# 2. Schedule 4 deliveries per day maximum  
# 3. Optimize delivery routes
# 4. Add donor pickups on return route

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from geopy.distance import great_circle
import random

class TFPSmartScheduler:
    def __init__(self):
        self.warehouse = [41.3, -96.0]  # TFP warehouse location
        self.max_deliveries_per_day = 4  # TFP's current capacity
        
        # Mock GPS coordinates for Omaha zip codes
        self.zip_coords = {
            '68104': [41.3114, -95.9208], '68111': [41.3456, -95.9017],
            '68134': [41.2072, -96.1003], '68106': [41.2033, -95.9778],
            '68127': [41.1544, -96.0142], '68137': [41.1836, -95.8975],
            '68108': [41.2203, -95.8608], '68114': [41.2203, -95.8608],
            '68124': [41.2500, -96.0500], '68132': [41.2203, -95.8608]
        }
    
    def get_coordinates(self, address):
        """Convert address to GPS coordinates using zip code"""
        for zip_code, coords in self.zip_coords.items():
            if zip_code in address:
                return coords
        return self.warehouse  # Default to warehouse if zip not found
    
    def load_client_preferences(self, csv_path='mock_client_scheduling.csv'):
        """Load client scheduling preferences"""
        df = pd.read_csv(csv_path)
        
        # Add GPS coordinates
        df['lat'] = df['address'].apply(lambda addr: self.get_coordinates(addr)[0])
        df['lon'] = df['address'].apply(lambda addr: self.get_coordinates(addr)[1])
        
        return df
    
    def load_donor_pickups(self, csv_path='mock_donor_pickups.csv'):
        """Load donor pickup requests"""
        df = pd.read_csv(csv_path)
        
        # Add GPS coordinates
        df['lat'] = df['address'].apply(lambda addr: self.get_coordinates(addr)[0])
        df['lon'] = df['address'].apply(lambda addr: self.get_coordinates(addr)[1])
        
        return df
    
    def schedule_daily_deliveries(self, client_prefs, target_date):
        """Schedule 4 deliveries for a specific date using client preferences"""
        
        # Get all clients who want delivery on this date
        date_requests = client_prefs[client_prefs['preferred_date'] == target_date].copy()
        
        if len(date_requests) == 0:
            return pd.DataFrame()
        
        # Sort by preference rank (1st choice gets priority)
        date_requests = date_requests.sort_values('preference_rank')
        
        # Group by client to avoid double-booking
        scheduled = []
        scheduled_clients = set()
        
        for _, request in date_requests.iterrows():
            if len(scheduled) >= self.max_deliveries_per_day:
                break
                
            if request['client_name'] not in scheduled_clients:
                scheduled.append(request)
                scheduled_clients.add(request['client_name'])
        
        if not scheduled:
            return pd.DataFrame()
        
        # Convert to DataFrame and optimize route
        scheduled_df = pd.DataFrame(scheduled)
        optimized_route = self.optimize_delivery_route(scheduled_df)
        
        return optimized_route
    
    def optimize_delivery_route(self, deliveries_df):
        """Optimize the order of deliveries using nearest neighbor"""
        if len(deliveries_df) <= 1:
            return deliveries_df
        
        # Start from warehouse
        current_location = self.warehouse
        optimized_order = []
        remaining = deliveries_df.copy()
        
        while len(remaining) > 0:
            # Find nearest delivery
            distances = remaining.apply(
                lambda row: great_circle(current_location, [row['lat'], row['lon']]).miles, 
                axis=1
            )
            nearest_idx = distances.idxmin()
            nearest_delivery = remaining.loc[nearest_idx]
            
            # Add to optimized route
            optimized_order.append(nearest_delivery)
            current_location = [nearest_delivery['lat'], nearest_delivery['lon']]
            
            # Remove from remaining
            remaining = remaining.drop(nearest_idx)
        
        return pd.DataFrame(optimized_order)
    
    def select_donor_pickups_on_route(self, donor_pickups, last_delivery_location, max_pickups=3):
        """Select donor pickups that are on the way back to warehouse"""
        if len(donor_pickups) == 0:
            return pd.DataFrame()
        
        # Calculate distances from last delivery to each donor
        distances = donor_pickups.apply(
            lambda row: great_circle(last_delivery_location, [row['lat'], row['lon']]).miles,
            axis=1
        )
        
        # Sort by distance and take closest ones
        donor_pickups_with_dist = donor_pickups.copy()
        donor_pickups_with_dist['distance_from_last_delivery'] = distances
        
        # Select up to max_pickups closest donors
        selected_pickups = donor_pickups_with_dist.sort_values('distance_from_last_delivery').head(max_pickups)
        
        # Optimize pickup order
        optimized_pickups = self.optimize_pickup_route(selected_pickups, last_delivery_location)
        
        return optimized_pickups
    
    def optimize_pickup_route(self, pickups_df, start_location):
        """Optimize the order of pickups from the last delivery location"""
        if len(pickups_df) <= 1:
            return pickups_df
        
        current_location = start_location
        optimized_order = []
        remaining = pickups_df.copy()
        
        while len(remaining) > 0:
            # Find nearest pickup
            distances = remaining.apply(
                lambda row: great_circle(current_location, [row['lat'], row['lon']]).miles,
                axis=1
            )
            nearest_idx = distances.idxmin()
            nearest_pickup = remaining.loc[nearest_idx]
            
            # Add to optimized route
            optimized_order.append(nearest_pickup)
            current_location = [nearest_pickup['lat'], nearest_pickup['lon']]
            
            # Remove from remaining
            remaining = remaining.drop(nearest_idx)
        
        return pd.DataFrame(optimized_order)
    
    def create_daily_schedule(self, target_date):
        """Create complete daily schedule: deliveries + pickups with optimized routes"""
        
        # Load data
        client_prefs = self.load_client_preferences()
        donor_pickups = self.load_donor_pickups()
        
        # Schedule deliveries (max 4 per day)
        scheduled_deliveries = self.schedule_daily_deliveries(client_prefs, target_date)
        
        if len(scheduled_deliveries) == 0:
            return {
                'date': target_date,
                'deliveries': pd.DataFrame(),
                'pickups': pd.DataFrame(),
                'total_distance': 0,
                'route_summary': "No deliveries scheduled for this date"
            }
        
        # Get last delivery location for pickup routing
        last_delivery = scheduled_deliveries.iloc[-1]
        last_delivery_location = [last_delivery['lat'], last_delivery['lon']]
        
        # Select and optimize donor pickups on the way back
        scheduled_pickups = self.select_donor_pickups_on_route(
            donor_pickups, last_delivery_location, max_pickups=3
        )
        
        # Calculate total route distance
        total_distance = self.calculate_total_distance(scheduled_deliveries, scheduled_pickups)
        
        return {
            'date': target_date,
            'deliveries': scheduled_deliveries,
            'pickups': scheduled_pickups,
            'total_distance': total_distance,
            'route_summary': f"{len(scheduled_deliveries)} deliveries + {len(scheduled_pickups)} pickups"
        }
    
    def calculate_total_distance(self, deliveries, pickups):
        """Calculate total driving distance for the complete route"""
        total_distance = 0
        current_location = self.warehouse
        
        # Distance through deliveries
        for _, delivery in deliveries.iterrows():
            delivery_location = [delivery['lat'], delivery['lon']]
            total_distance += great_circle(current_location, delivery_location).miles
            current_location = delivery_location
        
        # Distance through pickups
        for _, pickup in pickups.iterrows():
            pickup_location = [pickup['lat'], pickup['lon']]
            total_distance += great_circle(current_location, pickup_location).miles
            current_location = pickup_location
        
        # Distance back to warehouse
        total_distance += great_circle(current_location, self.warehouse).miles
        
        return round(total_distance, 1)
    
    def get_available_clients_for_date(self, target_date, exclude_scheduled=None, include_all_clients=False):
        """Get clients available for a specific date who aren't already scheduled"""
        client_prefs = self.load_client_preferences()
        
        if include_all_clients:
            # Get ALL unscheduled clients (TFP can move anyone to fill capacity)
            available = client_prefs.copy()
        else:
            # Get only clients who have this date as one of their preferences
            available = client_prefs[client_prefs['preferred_date'] == target_date].copy()
        
        # Exclude already scheduled clients
        if exclude_scheduled is not None and len(exclude_scheduled) > 0:
            scheduled_clients = set(exclude_scheduled['client_name'])
            available = available[~available['client_name'].isin(scheduled_clients)]
        
        return available
    
    def suggest_4th_delivery(self, current_deliveries, target_date):
        """Suggest best 4th delivery based on route optimization"""
        if len(current_deliveries) >= 4:
            return None
        
        # First try clients who want this specific date
        available_clients = self.get_available_clients_for_date(target_date, current_deliveries, include_all_clients=False)
        
        # If no clients want this date, get ALL available clients (TFP can reschedule anyone)
        if len(available_clients) == 0:
            available_clients = self.get_available_clients_for_date(target_date, current_deliveries, include_all_clients=True)
            
        if len(available_clients) == 0:
            return None
        
        # Test each available client to see which minimizes total distance
        best_client = None
        best_distance = float('inf')
        best_route = None
        
        for _, client in available_clients.iterrows():
            # Create test delivery set with this client added
            test_deliveries = pd.concat([current_deliveries, pd.DataFrame([client])], ignore_index=True)
            
            # Optimize route with this client
            optimized_test = self.optimize_delivery_route(test_deliveries)
            
            # Calculate total distance
            test_distance = self.calculate_total_distance(optimized_test, pd.DataFrame())
            
            # Check if this is the best option
            if test_distance < best_distance:
                best_distance = test_distance
                best_client = client
                best_route = optimized_test
        
        return {
            'suggested_client': best_client,
            'new_total_distance': best_distance,
            'optimized_route': best_route,
            'distance_increase': best_distance - self.calculate_total_distance(current_deliveries, pd.DataFrame())
        }
    
    def add_manual_delivery(self, current_schedule, client_name, target_date):
        """Manually add a specific client to the schedule and re-optimize"""
        client_prefs = self.load_client_preferences()
        
        # Find the client's preference for this date
        client_request = client_prefs[
            (client_prefs['client_name'] == client_name) & 
            (client_prefs['preferred_date'] == target_date)
        ]
        
        # If client doesn't have this date as preference, use their first preference but move to this date
        if len(client_request) == 0:
            client_any_date = client_prefs[client_prefs['client_name'] == client_name]
            if len(client_any_date) == 0:
                return None
            
            # Take their best preference but change the date
            best_pref = client_any_date.sort_values('preference_rank').iloc[0].copy()
            best_pref['preferred_date'] = target_date  # Move them to the target date
        else:
            # Take their best available preference for this date
            best_pref = client_request.sort_values('preference_rank').iloc[0]
        
        # Add to current deliveries
        new_deliveries = pd.concat([current_schedule['deliveries'], pd.DataFrame([best_pref])], ignore_index=True)
        
        # Re-optimize route
        optimized_deliveries = self.optimize_delivery_route(new_deliveries)
        
        # Get last delivery location for pickups
        last_delivery = optimized_deliveries.iloc[-1]
        last_delivery_location = [last_delivery['lat'], last_delivery['lon']]
        
        # Re-optimize pickups
        donor_pickups = self.load_donor_pickups()
        optimized_pickups = self.select_donor_pickups_on_route(
            donor_pickups, last_delivery_location, max_pickups=3
        )
        
        # Calculate new total distance
        new_distance = self.calculate_total_distance(optimized_deliveries, optimized_pickups)
        
        return {
            'date': current_schedule['date'],
            'deliveries': optimized_deliveries,
            'pickups': optimized_pickups,
            'total_distance': new_distance,
            'route_summary': f"{len(optimized_deliveries)} deliveries + {len(optimized_pickups)} pickups",
            'added_client': client_name
        }
    
    def print_daily_schedule(self, schedule):
        """Print formatted daily schedule"""
        print(f"\n📅 TFP Daily Schedule - {schedule['date']}")
        print("=" * 50)
        print(f"📊 Summary: {schedule['route_summary']}")
        print(f"🛣️  Total Distance: {schedule['total_distance']} miles")
        
        if len(schedule['deliveries']) > 0:
            print(f"\n📦 DELIVERIES ({len(schedule['deliveries'])}/4 max):")
            for i, (_, delivery) in enumerate(schedule['deliveries'].iterrows(), 1):
                print(f"  {i}. {delivery['client_name']} - {delivery['address']}")
                print(f"     Time: {delivery['preferred_time_slot']} | Phone: {delivery['phone']}")
        
        if len(schedule['pickups']) > 0:
            print(f"\n🏠 DONOR PICKUPS (on return route):")
            for i, (_, pickup) in enumerate(schedule['pickups'].iterrows(), 1):
                print(f"  {i}. {pickup['donor_name']} - {pickup['address']}")
                print(f"     Items: {pickup['furniture_items']} | Phone: {pickup['phone']}")
        
        print(f"\n🚛 Route: Warehouse → Deliveries → Pickups → Warehouse")

# Demo the system
if __name__ == "__main__":
    scheduler = TFPSmartScheduler()
    
    # Schedule for next few days
    start_date = datetime.now() + timedelta(days=1)
    
    for i in range(5):  # Show 5 days
        target_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        daily_schedule = scheduler.create_daily_schedule(target_date)
        scheduler.print_daily_schedule(daily_schedule)
        
        # Save to CSV
        if len(daily_schedule['deliveries']) > 0:
            filename = f"tfp_schedule_{target_date}.csv"
            
            # Combine deliveries and pickups
            all_stops = []
            
            # Add deliveries
            for _, delivery in daily_schedule['deliveries'].iterrows():
                all_stops.append({
                    'date': target_date,
                    'stop_type': 'delivery',
                    'client_name': delivery['client_name'],
                    'address': delivery['address'],
                    'phone': delivery['phone'],
                    'time_slot': delivery['preferred_time_slot'],
                    'items': delivery['furniture_items']
                })
            
            # Add pickups
            for _, pickup in daily_schedule['pickups'].iterrows():
                all_stops.append({
                    'date': target_date,
                    'stop_type': 'pickup',
                    'client_name': pickup['donor_name'],
                    'address': pickup['address'],
                    'phone': pickup['phone'],
                    'time_slot': 'Flexible',
                    'items': pickup['furniture_items']
                })
            
            pd.DataFrame(all_stops).to_csv(filename, index=False)
            print(f"💾 Schedule saved to {filename}")
    
    print(f"\n✅ Smart scheduling complete!")
    print(f"📋 Key Features:")
    print(f"   • Respects client time preferences")
    print(f"   • Maximum 4 deliveries per day")
    print(f"   • Optimized delivery routes")
    print(f"   • Smart pickup selection on return route")
    print(f"   • Minimizes total driving distance")