import pandas as pd
from datetime import datetime, timedelta, time
import streamlit as st

class CalendarScheduler:
    def __init__(self):
        self.time_slots = [
            "9:00 AM - 11:00 AM",
            "11:00 AM - 1:00 PM", 
            "1:00 PM - 3:00 PM",
            "3:00 PM - 5:00 PM"
        ]
        self.trucks_per_slot = 2  # 2 trucks available per time slot
    
    def get_available_slots(self, date, zone, size):
        """Get available time slots for a specific date, zone, and size"""
        # Mock availability (in production, check actual bookings)
        available_slots = []
        
        for slot in self.time_slots:
            # Check if slot has capacity for this zone and size
            slot_key = f"{date}_{zone}_{slot}"
            
            # Simple availability logic
            available_slots.append({
                'date': date,
                'time_slot': slot,
                'zone': zone,
                'size_allowed': size,
                'available': True,
                'truck_assigned': f"Truck_{zone + 1}"
            })
        
        return available_slots
    
    def book_slot(self, client_data, slot_info):
        """Book a time slot for a client"""
        booking = {
            'booking_id': f"TFP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'client_name': client_data['client_name'],
            'address': client_data['address'],
            'phone': client_data['phone'],
            'size': client_data['size'],
            'date': slot_info['date'],
            'time_slot': slot_info['time_slot'],
            'zone': slot_info['zone'],
            'truck': slot_info['truck_assigned'],
            'status': 'confirmed'
        }
        
        return booking
    
    def generate_weekly_calendar(self, start_date):
        """Generate a weekly calendar view"""
        calendar_data = []
        
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            
            for slot in self.time_slots:
                for zone in range(3):  # 3 zones
                    calendar_data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'day_name': current_date.strftime('%A'),
                        'time_slot': slot,
                        'zone': zone,
                        'truck': f"Truck_{zone + 1}",
                        'available_capacity': 'Available',
                        'bookings': 0
                    })
        
        return pd.DataFrame(calendar_data)

# Streamlit calendar interface
def show_calendar_interface():
    st.header("📅 Scheduling Calendar")
    
    scheduler = CalendarScheduler()
    
    # Date selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Week Starting", datetime.now())
    with col2:
        selected_zone = st.selectbox("Zone", [0, 1, 2], format_func=lambda x: f"Zone {x}")
    
    # Generate calendar
    calendar_df = scheduler.generate_weekly_calendar(start_date)
    zone_calendar = calendar_df[calendar_df['zone'] == selected_zone]
    
    # Display calendar
    st.subheader(f"Zone {selected_zone} - Truck {selected_zone + 1}")
    
    # Pivot table for calendar view
    calendar_pivot = zone_calendar.pivot(index='time_slot', columns='day_name', values='available_capacity')
    
    st.dataframe(calendar_pivot, use_container_width=True)
    
    # Booking form
    st.subheader("📝 New Booking")
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("Client Name")
            address = st.text_input("Address")
            phone = st.text_input("Phone")
        
        with col2:
            booking_date = st.date_input("Delivery Date")
            time_slot = st.selectbox("Time Slot", scheduler.time_slots)
            size = st.selectbox("Order Size", ['small', 'medium', 'large'])
        
        if st.form_submit_button("Book Slot"):
            if client_name and address:
                client_data = {
                    'client_name': client_name,
                    'address': address,
                    'phone': phone,
                    'size': size
                }
                
                slot_info = {
                    'date': booking_date.strftime('%Y-%m-%d'),
                    'time_slot': time_slot,
                    'zone': selected_zone,
                    'truck_assigned': f"Truck_{selected_zone + 1}"
                }
                
                booking = scheduler.book_slot(client_data, slot_info)
                st.success(f"✅ Booking confirmed! ID: {booking['booking_id']}")
                st.json(booking)
            else:
                st.error("Please fill in all required fields")

if __name__ == "__main__":
    show_calendar_interface()