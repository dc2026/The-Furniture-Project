import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from tfp_scheduling_system import TFPSchedulingSystem
from calendar_scheduler import CalendarScheduler, show_calendar_interface

st.set_page_config(page_title="TFP Complete Dashboard", layout="wide")

# Navigation
st.sidebar.title("🏠 The Furniture Project")
page = st.sidebar.selectbox("Navigate", [
    "📊 Dashboard Overview", 
    "📅 Calendar Scheduler", 
    "🚚 Route Optimizer",
    "📋 Daily Operations"
])

if page == "📊 Dashboard Overview":
    st.title("📊 TFP Operations Dashboard")
    
    # Load system
    system = TFPSchedulingSystem()
    
    try:
        requests_df = system.load_requests('Phase 3/furniture_project_requests - Request Assistance Form .csv')
        requests_df = system.assign_zones(requests_df, 3)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", len(requests_df))
        with col2:
            st.metric("Pending Deliveries", len(requests_df[requests_df['status'] == 'pending']))
        with col3:
            st.metric("Active Zones", requests_df['zone'].nunique())
        with col4:
            st.metric("Large Orders", len(requests_df[requests_df['size'] == 'large']))
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            size_dist = requests_df['size'].value_counts()
            fig = px.pie(values=size_dist.values, names=size_dist.index, title="Order Size Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            zone_dist = requests_df['zone'].value_counts().sort_index()
            fig = px.bar(x=[f"Zone {i}" for i in zone_dist.index], y=zone_dist.values, title="Requests by Zone")
            st.plotly_chart(fig, use_container_width=True)
        
        # Map
        st.subheader("🗺️ Request Locations")
        fig_map = px.scatter_mapbox(
            requests_df, lat='lat', lon='lon', color='size',
            zoom=10, mapbox_style="open-street-map",
            hover_data=['client_name', 'address']
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
    except FileNotFoundError:
        st.error("Data file not found. Please check file path.")

elif page == "📅 Calendar Scheduler":
    show_calendar_interface()

elif page == "🚚 Route Optimizer":
    st.title("🚚 Route Optimization")
    
    system = TFPSchedulingSystem()
    
    try:
        requests_df = system.load_requests('Phase 3/furniture_project_requests - Request Assistance Form .csv')
        requests_df = system.assign_zones(requests_df, 3)
        
        selected_zone = st.selectbox("Select Zone", requests_df['zone'].unique())
        
        if st.button("Optimize Route"):
            route_order, distance = system.optimize_route(requests_df, selected_zone)
            
            st.success(f"✅ Optimized route for Zone {selected_zone}")
            st.metric("Total Distance", f"{distance:.2f} miles")
            
            zone_requests = requests_df[requests_df['zone'] == selected_zone]
            st.subheader("Delivery Order")
            
            for i, idx in enumerate(route_order[1:-1], 1):  # Skip warehouse start/end
                if idx < len(zone_requests):
                    request = zone_requests.iloc[idx]
                    st.write(f"{i}. {request['client_name']} - {request['address']} ({request['size']})")
    
    except FileNotFoundError:
        st.error("Data file not found.")

elif page == "📋 Daily Operations":
    st.title("📋 Daily Operations")
    
    # Truck status
    st.subheader("🚛 Truck Status")
    
    truck_status = pd.DataFrame({
        'Truck': ['Truck 1', 'Truck 2', 'Truck 3'],
        'Zone': ['Zone 0', 'Zone 1', 'Zone 2'],
        'Status': ['Active', 'Loading', 'Available'],
        'Current Load': ['2/3 Small', '1/1 Large', '0/3 Small'],
        'Next Delivery': ['10:30 AM', '11:00 AM', 'Unscheduled']
    })
    
    st.dataframe(truck_status, use_container_width=True)
    
    # Today's schedule
    st.subheader("📅 Today's Schedule")
    
    today_schedule = pd.DataFrame({
        'Time': ['9:00 AM', '10:30 AM', '11:00 AM', '1:00 PM', '2:30 PM'],
        'Truck': ['Truck 1', 'Truck 1', 'Truck 2', 'Truck 3', 'Truck 1'],
        'Client': ['John Smith', 'Mary Johnson', 'Bob Wilson', 'Lisa Brown', 'Tom Davis'],
        'Address': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St', '654 Maple Dr'],
        'Size': ['Small', 'Medium', 'Large', 'Small', 'Small'],
        'Status': ['Completed', 'In Progress', 'Scheduled', 'Scheduled', 'Scheduled']
    })
    
    st.dataframe(today_schedule, use_container_width=True)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📞 Contact Next Client"):
            st.info("Calling Mary Johnson at (402) 555-0123...")
    
    with col2:
        if st.button("📍 Update Location"):
            st.info("Truck 1 location updated")
    
    with col3:
        if st.button("✅ Mark Complete"):
            st.success("Delivery marked as complete")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**The Furniture Project**")
st.sidebar.markdown("Serving 5,400+ people in 2024")
st.sidebar.markdown("170+ community partners")