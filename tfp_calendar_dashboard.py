# TFP Calendar Dashboard - Mimics Google Calendar System
# Interactive calendar for scheduling deliveries and pickups

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from tfp_smart_scheduler import TFPSmartScheduler

st.set_page_config(page_title="TFP Calendar Dashboard", layout="wide")

# Initialize scheduler
@st.cache_resource
def load_scheduler():
    return TFPSmartScheduler()

scheduler = load_scheduler()

# Header
st.title("📅 The Furniture Project - Calendar Dashboard")
st.markdown("**Smart scheduling system that mimics your current Google Calendar process**")

# Sidebar controls
st.sidebar.header("📋 Schedule Controls")
view_mode = st.sidebar.selectbox("View Mode", ["Weekly Calendar", "Daily Schedule", "Client Requests"])

if view_mode == "Weekly Calendar":
    st.header("📅 Weekly Calendar View")
    
    # Date picker
    start_date = st.date_input("Week Starting", datetime.now().date())
    
    # Generate week dates
    week_dates = [(start_date + timedelta(days=i)) for i in range(7)]
    
    # Create calendar grid
    cols = st.columns(7)
    
    for i, day_date in enumerate(week_dates):
        with cols[i]:
            # Day header
            day_name = day_date.strftime('%A')
            date_str = day_date.strftime('%m/%d')
            st.subheader(f"{day_name}\n{date_str}")
            
            # Get schedule for this day
            daily_schedule = scheduler.create_daily_schedule(day_date.strftime('%Y-%m-%d'))
            
            # Time slots
            time_slots = [
                "9:00 AM - 11:00 AM",
                "11:00 AM - 1:00 PM", 
                "1:00 PM - 3:00 PM",
                "3:00 PM - 5:00 PM"
            ]
            
            for slot in time_slots:
                # Check if this slot has deliveries
                slot_deliveries = []
                if len(daily_schedule['deliveries']) > 0:
                    slot_deliveries = daily_schedule['deliveries'][
                        daily_schedule['deliveries']['preferred_time_slot'] == slot
                    ]
                
                # Display slot
                if len(slot_deliveries) > 0:
                    for _, delivery in slot_deliveries.iterrows():
                        st.success(f"📦 {delivery['client_name']}\n{delivery['address'][:20]}...")
                else:
                    st.info(f"⏰ {slot}\n🔓 Available")
            
            # Show pickups
            if len(daily_schedule['pickups']) > 0:
                st.warning(f"🏠 {len(daily_schedule['pickups'])} Pickups\nOn return route")
            
            # Show total distance
            if daily_schedule['total_distance'] > 0:
                st.metric("Miles", f"{daily_schedule['total_distance']}")

elif view_mode == "Daily Schedule":
    st.header("📋 Daily Schedule Details")
    
    # Date picker
    selected_date = st.date_input("Select Date", datetime.now().date())
    
    # Get detailed schedule
    daily_schedule = scheduler.create_daily_schedule(selected_date.strftime('%Y-%m-%d'))
    
    if len(daily_schedule['deliveries']) == 0:
        st.info("No deliveries scheduled for this date")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Deliveries", f"{len(daily_schedule['deliveries'])}/4")
        with col2:
            st.metric("Pickups", len(daily_schedule['pickups']))
        with col3:
            st.metric("Total Miles", daily_schedule['total_distance'])
        with col4:
            est_time = daily_schedule['total_distance'] * 2.5 + len(daily_schedule['deliveries']) * 20 + len(daily_schedule['pickups']) * 30
            st.metric("Est. Time", f"{int(est_time)} min")
        
        # Deliveries section
        st.subheader("📦 Client Deliveries")
        deliveries_display = daily_schedule['deliveries'][['client_name', 'address', 'preferred_time_slot', 'phone', 'furniture_items']].copy()
        deliveries_display.columns = ['Client', 'Address', 'Time Slot', 'Phone', 'Items']
        st.dataframe(deliveries_display, use_container_width=True)
        
        # Pickups section
        if len(daily_schedule['pickups']) > 0:
            st.subheader("🏠 Donor Pickups (Return Route)")
            pickups_display = daily_schedule['pickups'][['donor_name', 'address', 'phone', 'furniture_items']].copy()
            pickups_display.columns = ['Donor', 'Address', 'Phone', 'Items']
            st.dataframe(pickups_display, use_container_width=True)
        
        # Route map (mock)
        st.subheader("🗺️ Optimized Route")
        
        # Create route visualization
        route_data = []
        
        # Add warehouse start
        route_data.append({
            'lat': scheduler.warehouse[0],
            'lon': scheduler.warehouse[1],
            'name': 'TFP Warehouse (Start)',
            'type': 'warehouse',
            'order': 0
        })
        
        # Add deliveries
        for i, (_, delivery) in enumerate(daily_schedule['deliveries'].iterrows()):
            route_data.append({
                'lat': delivery['lat'],
                'lon': delivery['lon'],
                'name': f"{delivery['client_name']} - {delivery['preferred_time_slot']}",
                'type': 'delivery',
                'order': i + 1
            })
        
        # Add pickups
        for i, (_, pickup) in enumerate(daily_schedule['pickups'].iterrows()):
            route_data.append({
                'lat': pickup['lat'],
                'lon': pickup['lon'],
                'name': f"{pickup['donor_name']} (Pickup)",
                'type': 'pickup',
                'order': len(daily_schedule['deliveries']) + i + 1
            })
        
        # Add warehouse end
        route_data.append({
            'lat': scheduler.warehouse[0],
            'lon': scheduler.warehouse[1],
            'name': 'TFP Warehouse (Return)',
            'type': 'warehouse',
            'order': len(route_data)
        })
        
        route_df = pd.DataFrame(route_data)
        
        # Create map
        fig = px.scatter_mapbox(
            route_df,
            lat='lat',
            lon='lon',
            color='type',
            size_max=15,
            zoom=10,
            mapbox_style="open-street-map",
            hover_name='name',
            title="Daily Route Map"
        )
        
        # Add route line
        fig.add_trace(go.Scattermapbox(
            lat=route_df['lat'],
            lon=route_df['lon'],
            mode='lines',
            line=dict(width=3, color='red'),
            name='Route'
        ))
        
        st.plotly_chart(fig, use_container_width=True)

elif view_mode == "Client Requests":
    st.header("📝 Client Scheduling Requests")
    
    # Load client preferences
    try:
        client_prefs = scheduler.load_client_preferences()
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requests", len(client_prefs))
        with col2:
            st.metric("Unique Clients", client_prefs['client_name'].nunique())
        with col3:
            pending = len(client_prefs[client_prefs['status'] == 'pending_scheduling'])
            st.metric("Pending", pending)
        
        # Filter options
        st.subheader("🔍 Filter Requests")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_client = st.selectbox(
                "Select Client", 
                ['All'] + list(client_prefs['client_name'].unique())
            )
        
        with col2:
            selected_date = st.selectbox(
                "Select Date",
                ['All'] + list(client_prefs['preferred_date'].unique())
            )
        
        # Apply filters
        filtered_prefs = client_prefs.copy()
        if selected_client != 'All':
            filtered_prefs = filtered_prefs[filtered_prefs['client_name'] == selected_client]
        if selected_date != 'All':
            filtered_prefs = filtered_prefs[filtered_prefs['preferred_date'] == selected_date]
        
        # Display requests
        st.subheader("📋 Scheduling Preferences")
        display_cols = ['client_name', 'preferred_date', 'preferred_time_slot', 'preference_rank', 'phone', 'furniture_items', 'status']
        display_names = ['Client', 'Date', 'Time Slot', 'Preference', 'Phone', 'Items', 'Status']
        
        display_df = filtered_prefs[display_cols].copy()
        display_df.columns = display_names
        
        st.dataframe(display_df, use_container_width=True)
        
        # Client preference analysis
        if selected_client != 'All':
            st.subheader(f"📊 {selected_client}'s Preferences")
            client_data = client_prefs[client_prefs['client_name'] == selected_client]
            
            for _, pref in client_data.iterrows():
                rank_emoji = ["🥇", "🥈", "🥉"][pref['preference_rank'] - 1]
                st.write(f"{rank_emoji} **Choice {pref['preference_rank']}**: {pref['preferred_date']} at {pref['preferred_time_slot']}")
    
    except FileNotFoundError:
        st.error("Client preference data not found. Please run the mock data generator first.")

# Footer with quick actions
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Quick Actions")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_resource.clear()
    st.rerun()

if st.sidebar.button("📊 Generate Weekly Schedule"):
    st.sidebar.success("Generating optimized schedules...")
    # This would trigger the scheduling algorithm

if st.sidebar.button("📧 Send Notifications"):
    st.sidebar.info("Sending client confirmations...")

# System info
st.sidebar.markdown("---")
st.sidebar.markdown("**📈 System Stats**")
st.sidebar.markdown("• Max 4 deliveries/day")
st.sidebar.markdown("• Route optimization enabled")
st.sidebar.markdown("• Client preferences respected")
st.sidebar.markdown("• Donor pickups on return route")