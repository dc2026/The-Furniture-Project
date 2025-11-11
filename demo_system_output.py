# Demo: What the TFP Smart Scheduler System Looks Like When Running

from tfp_smart_scheduler import TFPSmartScheduler
from datetime import datetime, timedelta

def demo_system_output():
    """Show what the system looks like when it runs"""
    
    print("🏠 THE FURNITURE PROJECT - SMART SCHEDULER DEMO")
    print("=" * 60)
    
    scheduler = TFPSmartScheduler()
    
    # Show what happens for one day
    target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n🎯 SCHEDULING FOR: {target_date}")
    print("-" * 40)
    
    # Step 1: Load client preferences
    print("📋 STEP 1: Loading client preferences...")
    client_prefs = scheduler.load_client_preferences()
    print(f"   ✅ Loaded {len(client_prefs)} client time preferences")
    print(f"   ✅ {client_prefs['client_name'].nunique()} unique clients")
    
    # Step 2: Load donor pickups
    print("\n🏠 STEP 2: Loading donor pickup requests...")
    donor_pickups = scheduler.load_donor_pickups()
    print(f"   ✅ Loaded {len(donor_pickups)} donor pickup requests")
    
    # Step 3: Create daily schedule
    print(f"\n📅 STEP 3: Creating optimized schedule for {target_date}...")
    daily_schedule = scheduler.create_daily_schedule(target_date)
    
    if len(daily_schedule['deliveries']) == 0:
        print("   ⚠️  No client requests for this date")
        return
    
    print(f"   ✅ Scheduled {len(daily_schedule['deliveries'])} deliveries")
    print(f"   ✅ Added {len(daily_schedule['pickups'])} donor pickups on return route")
    print(f"   ✅ Total route distance: {daily_schedule['total_distance']} miles")
    
    # Step 4: Show the actual schedule
    print(f"\n📦 CLIENT DELIVERIES ({len(daily_schedule['deliveries'])}/4 max):")
    print("-" * 40)
    
    for i, (_, delivery) in enumerate(daily_schedule['deliveries'].iterrows(), 1):
        print(f"   {i}. 📍 {delivery['client_name']}")
        print(f"      📍 {delivery['address']}")
        print(f"      ⏰ {delivery['preferred_time_slot']}")
        print(f"      📞 {delivery['phone']}")
        print(f"      📦 {delivery['furniture_items']}")
        print()
    
    if len(daily_schedule['pickups']) > 0:
        print(f"🏠 DONOR PICKUPS (on return route):")
        print("-" * 40)
        
        for i, (_, pickup) in enumerate(daily_schedule['pickups'].iterrows(), 1):
            print(f"   {i}. 🏠 {pickup['donor_name']}")
            print(f"      📍 {pickup['address']}")
            print(f"      📞 {pickup['phone']}")
            print(f"      📦 {pickup['furniture_items']}")
            print(f"      📝 {pickup['pickup_notes']}")
            print()
    
    # Step 5: Show route summary
    print("🛣️  ROUTE SUMMARY:")
    print("-" * 40)
    print(f"   🏢 Start: TFP Warehouse")
    
    for i, (_, delivery) in enumerate(daily_schedule['deliveries'].iterrows(), 1):
        print(f"   📦 Stop {i}: {delivery['client_name']} ({delivery['preferred_time_slot']})")
    
    for i, (_, pickup) in enumerate(daily_schedule['pickups'].iterrows(), 1):
        stop_num = len(daily_schedule['deliveries']) + i
        print(f"   🏠 Stop {stop_num}: {pickup['donor_name']} (Pickup)")
    
    print(f"   🏢 End: TFP Warehouse")
    print(f"   📏 Total Distance: {daily_schedule['total_distance']} miles")
    
    # Step 6: Show what gets saved
    print(f"\n💾 FILES CREATED:")
    print("-" * 40)
    print(f"   📄 tfp_schedule_{target_date}.csv")
    print(f"   📊 Contains all stops with addresses, phones, times")
    print(f"   📋 Ready to import into Google Calendar or other systems")
    
    print(f"\n✅ SCHEDULING COMPLETE!")
    print(f"🎯 Key Benefits:")
    print(f"   • Respects client time preferences")
    print(f"   • Maximum 4 deliveries per day (TFP's capacity)")
    print(f"   • Optimized route reduces driving time")
    print(f"   • Smart pickup selection on return route")
    print(f"   • Automated scheduling replaces manual work")

if __name__ == "__main__":
    demo_system_output()