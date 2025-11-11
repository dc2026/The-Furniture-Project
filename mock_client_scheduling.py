# Mock Client Scheduling System for TFP
# Simulates clients selecting 3 preferred time slots for delivery

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_mock_client_scheduling_data():
    """Create mock data showing clients selecting 3 preferred delivery time slots"""
    
    # Time slots TFP offers (example)
    time_slots = [
        "9:00 AM - 11:00 AM",
        "11:00 AM - 1:00 PM", 
        "1:00 PM - 3:00 PM",
        "3:00 PM - 5:00 PM"
    ]
    
    # Generate dates for next 2 weeks
    start_date = datetime.now()
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
    
    # Mock client data
    clients = [
        {"name": "John Smith", "address": "123 Main St, Omaha NE 68104", "phone": "(402) 555-0101"},
        {"name": "Mary Johnson", "address": "456 Oak Ave, Omaha NE 68111", "phone": "(402) 555-0102"},
        {"name": "Bob Wilson", "address": "789 Pine Rd, Omaha NE 68134", "phone": "(402) 555-0103"},
        {"name": "Lisa Brown", "address": "321 Elm St, Omaha NE 68106", "phone": "(402) 555-0104"},
        {"name": "Tom Davis", "address": "654 Maple Dr, Omaha NE 68127", "phone": "(402) 555-0105"},
        {"name": "Sarah Miller", "address": "987 Cedar Ln, Omaha NE 68137", "phone": "(402) 555-0106"},
        {"name": "Mike Garcia", "address": "147 Birch St, Omaha NE 68108", "phone": "(402) 555-0107"},
        {"name": "Emma Wilson", "address": "258 Ash Ave, Omaha NE 68114", "phone": "(402) 555-0108"},
        {"name": "David Lee", "address": "369 Walnut Rd, Omaha NE 68124", "phone": "(402) 555-0109"},
        {"name": "Anna Taylor", "address": "741 Cherry St, Omaha NE 68132", "phone": "(402) 555-0110"}
    ]
    
    scheduling_requests = []
    
    for i, client in enumerate(clients):
        # Each client selects 3 preferred time slots
        preferred_slots = random.sample(time_slots, 3)
        preferred_dates = random.sample(dates[:7], 3)  # Pick from first week
        
        for j, (date, slot) in enumerate(zip(preferred_dates, preferred_slots)):
            scheduling_requests.append({
                'request_id': f"REQ_{i+1:03d}",
                'client_name': client['name'],
                'address': client['address'],
                'phone': client['phone'],
                'preferred_date': date,
                'preferred_time_slot': slot,
                'preference_rank': j + 1,  # 1st, 2nd, 3rd choice
                'furniture_items': random.choice([
                    "Queen bed set, dresser",
                    "Sofa, coffee table, lamp",
                    "Kitchen table, 4 chairs",
                    "Twin bed, nightstand",
                    "Bookshelf, desk, chair"
                ]),
                'status': 'pending_scheduling'
            })
    
    return pd.DataFrame(scheduling_requests)

def create_mock_donor_pickup_data():
    """Create mock data for donor furniture pickups"""
    
    donors = [
        {"name": "Jennifer Adams", "address": "159 Spruce St, Omaha NE 68104", "phone": "(402) 555-0201"},
        {"name": "Robert Clark", "address": "753 Poplar Ave, Omaha NE 68111", "phone": "(402) 555-0202"},
        {"name": "Michelle White", "address": "864 Hickory Rd, Omaha NE 68134", "phone": "(402) 555-0203"},
        {"name": "James Martinez", "address": "951 Sycamore St, Omaha NE 68106", "phone": "(402) 555-0204"},
        {"name": "Linda Rodriguez", "address": "357 Magnolia Dr, Omaha NE 68127", "phone": "(402) 555-0205"}
    ]
    
    pickup_requests = []
    
    for i, donor in enumerate(donors):
        pickup_requests.append({
            'pickup_id': f"PICKUP_{i+1:03d}",
            'donor_name': donor['name'],
            'address': donor['address'],
            'phone': donor['phone'],
            'available_dates': "Flexible - any weekday",
            'furniture_items': random.choice([
                "Dining room set (table + 6 chairs)",
                "Living room set (sofa, loveseat, coffee table)",
                "Bedroom set (queen bed, dresser, nightstands)",
                "Office furniture (desk, chair, bookshelf)",
                "Kitchen appliances and small furniture"
            ]),
            'pickup_notes': random.choice([
                "Second floor apartment - need help carrying down",
                "Items in garage - easy access",
                "Large items - may need truck",
                "Multiple small items",
                "Ground floor - easy pickup"
            ]),
            'status': 'available_for_pickup'
        })
    
    return pd.DataFrame(pickup_requests)

if __name__ == "__main__":
    # Generate mock data
    client_scheduling = create_mock_client_scheduling_data()
    donor_pickups = create_mock_donor_pickup_data()
    
    # Save to CSV files
    client_scheduling.to_csv('mock_client_scheduling.csv', index=False)
    donor_pickups.to_csv('mock_donor_pickups.csv', index=False)
    
    print("📅 Mock Client Scheduling Data Created:")
    print(f"   - {len(client_scheduling)} scheduling preferences")
    print(f"   - {len(client_scheduling['client_name'].unique())} unique clients")
    print(f"   - Each client provided 3 preferred time slots")
    
    print("\n🏠 Mock Donor Pickup Data Created:")
    print(f"   - {len(donor_pickups)} pickup requests")
    print(f"   - Available for flexible scheduling")
    
    print("\n📋 Sample Client Preferences:")
    sample_client = client_scheduling[client_scheduling['client_name'] == 'John Smith']
    for _, row in sample_client.iterrows():
        print(f"   {row['preference_rank']}. {row['preferred_date']} at {row['preferred_time_slot']}")
    
    print("\n📦 Files saved:")
    print("   - mock_client_scheduling.csv")
    print("   - mock_donor_pickups.csv")