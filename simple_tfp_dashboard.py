# Simple TFP Dashboard - Easy to Understand
# This dashboard shows your furniture delivery scheduling system

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from tfp_smart_scheduler import TFPSmartScheduler

# Set up the page
st.set_page_config(page_title="TFP Simple Dashboard", layout="wide")
st.title("🏠 The Furniture Project - Simple Dashboard")

# Create a sidebar menu
st.sidebar.title("📋 Menu")
page = st.sidebar.radio("Choose what to view:", [
    "📅 This Week's Schedule",
    "📝 Client Requests", 
    "🚚 Daily Route Details"
])

# Initialize the scheduler
scheduler = TFPSmartScheduler()

# Explain what colors mean
st.sidebar.markdown("---")
st.sidebar.markdown("**🎨 Color Guide:**")
st.sidebar.markdown("🟢 **Green** = Scheduled delivery")
st.sidebar.markdown("🔵 **Blue** = Available time slot")
st.sidebar.markdown("🟡 **Yellow** = Donor pickup")
st.sidebar.markdown("🔴 **Red** = Route line on map")

if page == "📅 This Week's Schedule":
    st.header("📅 This Week's Delivery Schedule")
    st.markdown("**This shows when deliveries are scheduled, just like your Google Calendar**")
    
    # Show today's date
    today = datetime.now().date()
    st.write(f"Today is: {today.strftime('%A, %B %d, %Y')}")
    
    # Create 7 columns for the week
    st.subheader("Weekly View")
    cols = st.columns(7)
    
    # Show each day of the week
    for i in range(7):
        day_date = today + timedelta(days=i)
        day_name = day_date.strftime('%A')
        
        with cols[i]:
            st.write(f"**{day_name}**")
            st.write(f"{day_date.strftime('%m/%d')}")
            
            # Get schedule for this day
            schedule = scheduler.create_daily_schedule(day_date.strftime('%Y-%m-%d'))
            
            # Show time slots
            time_slots = [
                "9:00 AM - 11:00 AM",
                "11:00 AM - 1:00 PM", 
                "1:00 PM - 3:00 PM",
                "3:00 PM - 5:00 PM"
            ]
            
            # Check if we have deliveries
            if len(schedule['deliveries']) > 0:
                # Show scheduled deliveries
                for _, delivery in schedule['deliveries'].iterrows():
                    st.success(f"✅ {delivery['client_name']}")
                
                # Show pickups if any
                if len(schedule['pickups']) > 0:
                    st.warning(f"🏠 {len(schedule['pickups'])} pickups")
                
                # Show total miles
                st.info(f"🚗 {schedule['total_distance']} miles")
            else:
                st.info("🔓 No deliveries\nscheduled")

elif page == "📝 Client Requests":
    st.header("📝 Client Scheduling Requests")
    st.markdown("**This shows all the clients who want furniture delivered and their preferred times**")
    
    try:
        # Load client preferences
        client_prefs = scheduler.load_client_preferences()
        
        # Show summary numbers
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Clients", len(client_prefs))
        with col2:
            unique_clients = client_prefs['client_name'].nunique()
            st.metric("Unique People", unique_clients)
        with col3:
            pending = len(client_prefs[client_prefs['status'] == 'pending_scheduling'])
            st.metric("Waiting for Schedule", pending)
        
        # Show the requests in a simple table
        st.subheader("📋 All Client Requests")
        st.markdown("**Each client gives us 3 preferred times (1st choice, 2nd choice, 3rd choice)**")
        
        # Make the table easier to read
        display_data = client_prefs[['client_name', 'preferred_date', 'preferred_time_slot', 'preference_rank', 'phone', 'furniture_items']].copy()
        display_data.columns = ['Client Name', 'Date Wanted', 'Time Slot', 'Choice #', 'Phone', 'Furniture Needed']
        
        # Add emoji for choice ranking
        display_data['Choice #'] = display_data['Choice #'].map({1: '🥇 1st Choice', 2: '🥈 2nd Choice', 3: '🥉 3rd Choice'})
        
        st.dataframe(display_data, use_container_width=True)
        
        # Explain what this means
        st.markdown("---")
        st.markdown("**💡 How it works:**")
        st.markdown("1. Clients fill out a form with 3 preferred delivery times")
        st.markdown("2. We try to schedule their 1st choice first")
        st.markdown("3. If that's full, we use their 2nd or 3rd choice")
        st.markdown("4. We can only do 4 deliveries per day maximum")
        
    except FileNotFoundError:
        st.error("❌ No client data found. Please run the system first to generate sample data.")

elif page == "🚚 Daily Route Details":
    st.header("🚚 Daily Route Details")
    st.markdown("**This shows the exact route for a specific day, including the map**")
    
    # Let user pick a date
    selected_date = st.date_input("Pick a date to see the route:", datetime.now().date())
    
    # Get the schedule for that date
    schedule = scheduler.create_daily_schedule(selected_date.strftime('%Y-%m-%d'))
    
    if len(schedule['deliveries']) == 0:
        st.info(f"📅 No deliveries scheduled for {selected_date.strftime('%A, %B %d, %Y')}")
    else:
        # Show summary
        st.success(f"✅ Found {len(schedule['deliveries'])} deliveries scheduled!")
        
        # Show metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Deliveries", f"{len(schedule['deliveries'])}/4")
        with col2:
            st.metric("Pickups", len(schedule['pickups']))
        with col3:
            st.metric("Total Miles", schedule['total_distance'])
        with col4:
            # Estimate time (2.5 min per mile + 20 min per delivery + 30 min per pickup)
            est_time = schedule['total_distance'] * 2.5 + len(schedule['deliveries']) * 20 + len(schedule['pickups']) * 30
            st.metric("Est. Time", f"{int(est_time)} min")
        
        # Debug info
        st.write(f"**Debug:** Found {len(schedule['deliveries'])} deliveries in schedule")
        
        # Show the delivery list
        st.subheader("📦 Deliveries (in order)")
        st.markdown("**The truck will visit these clients in this order to minimize driving:**")
        
        for i, (_, delivery) in enumerate(schedule['deliveries'].iterrows(), 1):
            st.write(f"**{i}. {delivery['client_name']}**")
            st.write(f"   📍 {delivery['address']}")
            st.write(f"   ⏰ {delivery['preferred_time_slot']}")
            st.write(f"   📞 {delivery['phone']}")
            st.write(f"   🛋️ {delivery['furniture_items']}")
            st.write("")
        
        # Add 4th delivery option if less than 4
        if len(schedule['deliveries']) < 4:
            st.markdown("---")
            st.subheader("➕ Add 4th Delivery")
            st.markdown(f"**Only {len(schedule['deliveries'])} deliveries scheduled. You can add 1 more:**")
            
            # Get suggestion
            suggestion = scheduler.suggest_4th_delivery(schedule['deliveries'], selected_date.strftime('%Y-%m-%d'))
            
            if suggestion:
                st.markdown("🤖 **AI Suggestion (Best Route Optimization):**")
                client = suggestion['suggested_client']
                distance_increase = suggestion['distance_increase']
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"⭐ **{client['client_name']}**\n📍 {client['address']}\n⏰ {client['preferred_time_slot']}\n🚗 +{distance_increase:.1f} miles")
                with col2:
                    if st.button("✅ Add This Client"):
                        # Add the suggested client
                        new_schedule = scheduler.add_manual_delivery(schedule, client['client_name'], selected_date.strftime('%Y-%m-%d'))
                        if new_schedule:
                            st.success(f"✅ Added {client['client_name']} to schedule!")
                            st.rerun()
                
                # Show other available options
                available_clients = scheduler.get_available_clients_for_date(selected_date.strftime('%Y-%m-%d'), schedule['deliveries'])
                
                if len(available_clients) > 1:
                    st.markdown("📋 **Other Available Clients:**")
                    other_clients = available_clients[available_clients['client_name'] != client['client_name']]['client_name'].unique()
                    
                    selected_manual = st.selectbox("Choose different client:", ['Select a client...'] + list(other_clients))
                    
                    if selected_manual != 'Select a client...' and st.button("➕ Add Selected Client"):
                        new_schedule = scheduler.add_manual_delivery(schedule, selected_manual, selected_date.strftime('%Y-%m-%d'))
                        if new_schedule:
                            st.success(f"✅ Added {selected_manual} to schedule!")
                            st.rerun()
                        else:
                            st.error(f"Could not add {selected_manual} - they may not have this date as a preference.")
            else:
                st.info("📋 No additional clients available for this date.")
        
        # Show pickups if any
        if len(schedule['pickups']) > 0:
            st.subheader("🏠 Donor Pickups (on the way back)")
            st.markdown("**After deliveries, the truck will pick up donated furniture:**")
            
            for i, (_, pickup) in enumerate(schedule['pickups'].iterrows(), 1):
                st.write(f"**{i}. {pickup['donor_name']}**")
                st.write(f"   📍 {pickup['address']}")
                st.write(f"   📞 {pickup['phone']}")
                st.write(f"   🛋️ {pickup['furniture_items']}")
                st.write("")
        
        # Explain the route
        st.markdown("---")
        st.markdown("**🗺️ Route Explanation:**")
        st.markdown("1. **Start** at TFP Warehouse")
        st.markdown("2. **Deliver** to clients (in optimized order)")
        st.markdown("3. **Pick up** donated furniture (on the way back)")
        st.markdown("4. **Return** to TFP Warehouse")
        st.markdown(f"5. **Total driving:** {schedule['total_distance']} miles")

# Footer with helpful info
st.sidebar.markdown("---")
st.sidebar.markdown("**ℹ️ About This System:**")
st.sidebar.markdown("• Replaces manual Google Calendar")
st.sidebar.markdown("• Automatically optimizes routes")
st.sidebar.markdown("• Respects client preferences")
st.sidebar.markdown("• Limits to 4 deliveries per day")
st.sidebar.markdown("• Adds pickups on return trips")

# Quick refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()