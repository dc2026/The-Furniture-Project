# daily_truck_scheduler.py
# Realistic daily truck scheduling: 2 trucks per day, 1-3 deliveries + 1-3 pickups each

import pandas as pd
from datetime import datetime, timedelta

class DailyTruckScheduler:
    def __init__(self):
        self.trucks_per_day = 2
        self.max_deliveries_per_truck = 3
        self.max_pickups_per_truck = 3
        
    def load_data(self):
        """Load cleaned request data"""
        try:
            self.df = pd.read_csv("data/master_requests.csv")
            return True
        except FileNotFoundError:
            print("Run clean_data.py first")
            return False
    
    def create_daily_schedule(self, start_date="2024-01-15", days=10):
        """Create realistic daily truck schedule"""
        if not self.load_data():
            return None
            
        # Separate pickups and deliveries
        pickups = self.df[self.df['request_type'] == 'pickup'].copy()
        deliveries = self.df[self.df['request_type'] != 'pickup'].copy()
        
        schedule = []
        pickup_index = 0
        delivery_index = 0
        
        for day in range(days):
            date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day)).strftime("%Y-%m-%d")
            
            # Schedule 2 trucks per day
            for truck_num in range(1, self.trucks_per_day + 1):
                truck_id = f"Daily_Truck_{truck_num}"
                
                # Assign 1-3 deliveries
                truck_deliveries = []
                delivery_count = min(3, len(deliveries) - delivery_index)
                for i in range(delivery_count):
                    if delivery_index < len(deliveries):
                        truck_deliveries.append(deliveries.iloc[delivery_index])
                        delivery_index += 1
                
                # Assign 1-3 pickups
                truck_pickups = []
                pickup_count = min(3, len(pickups) - pickup_index)
                for i in range(pickup_count):
                    if pickup_index < len(pickups):
                        truck_pickups.append(pickups.iloc[pickup_index])
                        pickup_index += 1
                
                # Create truck schedule if has any stops
                if truck_deliveries or truck_pickups:
                    schedule.append({
                        'date': date,
                        'truck_id': truck_id,
                        'deliveries': len(truck_deliveries),
                        'pickups': len(truck_pickups),
                        'total_stops': len(truck_deliveries) + len(truck_pickups),
                        'delivery_addresses': [d['Full Address'] for d in truck_deliveries],
                        'pickup_addresses': [p['Full Address'] for p in truck_pickups]
                    })
                
                # Stop if all requests assigned
                if delivery_index >= len(deliveries) and pickup_index >= len(pickups):
                    return schedule
        
        return schedule
    
    def save_daily_schedule(self, schedule):
        """Save daily schedule to CSV"""
        if not schedule:
            return
            
        # Create detailed schedule
        detailed_schedule = []
        for truck in schedule:
            # Add delivery stops
            for i, addr in enumerate(truck['delivery_addresses'], 1):
                detailed_schedule.append({
                    'date': truck['date'],
                    'truck_id': truck['truck_id'],
                    'stop_sequence': i,
                    'stop_type': 'delivery',
                    'address': addr,
                    'total_deliveries': truck['deliveries'],
                    'total_pickups': truck['pickups']
                })
            
            # Add pickup stops
            for i, addr in enumerate(truck['pickup_addresses'], truck['deliveries'] + 1):
                detailed_schedule.append({
                    'date': truck['date'],
                    'truck_id': truck['truck_id'],
                    'stop_sequence': i,
                    'stop_type': 'pickup',
                    'address': addr,
                    'total_deliveries': truck['deliveries'],
                    'total_pickups': truck['pickups']
                })
        
        pd.DataFrame(detailed_schedule).to_csv("data/daily_truck_schedule.csv", index=False)
        
        # Create summary
        summary_data = []
        for truck in schedule:
            summary_data.append({
                'date': truck['date'],
                'truck_id': truck['truck_id'],
                'deliveries': truck['deliveries'],
                'pickups': truck['pickups'],
                'total_stops': truck['total_stops']
            })
        
        pd.DataFrame(summary_data).to_csv("data/daily_summary.csv", index=False)
        
        print(f"Daily truck schedule saved to: data/daily_truck_schedule.csv")
        print(f"Daily summary saved to: data/daily_summary.csv")

# Run the daily scheduler
if __name__ == "__main__":
    scheduler = DailyTruckScheduler()
    schedule = scheduler.create_daily_schedule()
    
    if schedule:
        scheduler.save_daily_schedule(schedule)
        
        print(f"\nDaily Truck Schedule Summary:")
        print(f"Total days needed: {len(set(s['date'] for s in schedule))}")
        print(f"Total truck trips: {len(schedule)}")
        
        # Show first few days
        print(f"\nSample Schedule:")
        for truck in schedule[:6]:  # Show first 6 truck trips
            print(f"{truck['date']} - {truck['truck_id']}: {truck['deliveries']} deliveries, {truck['pickups']} pickups")
    else:
        print("No schedule created. Check data files.")