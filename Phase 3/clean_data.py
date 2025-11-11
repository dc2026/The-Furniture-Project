# clean_data.py
# Phase 3 - Data Cleaning for The Furniture Project
# This script prepares the raw Furniture Project dataset for scheduling and optimization.
# It keeps only relevant columns, classifies request sizes, flags pickup vs delivery,
# and saves a clean file for the backend and dashboard parts of the project.

import pandas as pd

# === Step 1: Load dataset ===
# Load the raw CSV file exported from Google Sheets
# This is the source data containing all furniture assistance requests
raw_path = "Copy of Data Capstone - Sample data - Request Assistance Form .csv"
df = pd.read_csv(raw_path)
print("Loaded:", df.shape[0], "rows,", df.shape[1], "columns")

# === Step 2: Select relevant columns ===
# Filter columns to only keep furniture-related and location data needed for scheduling
# This reduces file size and focuses on relevant data for optimization
keep_keywords = [
    "city", "zip", "address", "request", "item",
    "bed", "dresser", "table", "chair", "couch", "sofa", "mattress", "crib",
    "lamp", "nightstand", "bookcase", "shelf", "comforter",
    "pack", "high chair", "stroller", "pickup", "delivery"
]

# Find columns that contain any of our keywords
relevant_cols = [c for c in df.columns if any(k in c.lower() for k in keep_keywords)]

# Include these core location columns if they exist in the data
for col in [
    "Client's City and State",
    "Client's Zip Code", 
    "Is your client requesting"
]:
    if col in df.columns and col not in relevant_cols:
        relevant_cols.append(col)

# Keep only the relevant columns to reduce data size
df = df[relevant_cols].copy()
print("Kept", len(relevant_cols), "columns.")
print("Columns kept for cleaning:", relevant_cols)

# === Step 3: Clean data ===
# Remove invalid entries that would break routing and scheduling
# ZIP codes are essential for geographic grouping and route optimization
df["Client's Zip Code"] = df["Client's Zip Code"].astype(str).str.strip()
df = df.dropna(subset=["Client's Zip Code"])

# Remove completely empty rows and duplicate entries
df = df.dropna(how="all")
df = df.drop_duplicates()

# === Step 4: Combine City + Zip into one full address column ===
# Create standardized address format for geocoding and route planning
# This format is used by mapping and distance calculation functions
df["Full Address"] = (
    df["Client's City and State"].astype(str).str.strip()
    + ", "
    + df["Client's Zip Code"].astype(str).str.strip()
)

# === Step 5: Combine all furniture-related columns into one text field ===
# Merge all furniture item columns into single searchable text for classification
# This allows the size classification algorithm to analyze all requested items together
item_cols = [
    c for c in df.columns
    if c not in ["Client's City and State", "Client's Zip Code", "Full Address"]
]
df["combined_items"] = df[item_cols].astype(str).apply(lambda x: " ".join(x), axis=1)

# === Step 6: Classify size (small, medium, large) ===
# Simple size classification based on common furniture types
# Size categories correspond to truck capacity: 3 small OR 2 medium OR 1 large

def classify_size(text):
    """Simple furniture size classification
    
    Args:
        text (str): Combined text of all furniture items in request
        
    Returns:
        str: 'small', 'medium', or 'large' based on truck capacity requirements
    """
    # Convert to lowercase for easier matching
    text = str(text).lower()
    
    # LARGE items - Need truck/multiple people, fill truck capacity (1 per truck max)
    large_items = [
        'bed', 'mattress', 'sofa', 'couch', 'sectional', 'loveseat',
        'crib', 'dining set', 'bedroom set', 'living room set'
    ]
    
    # MEDIUM items - Need 2 people, moderate truck space (2 per truck max)
    medium_items = [
        'dresser', 'table', 'desk', 'bookshelf', 'tv stand', 
        'nightstand', 'cabinet', 'chest'
    ]
    
    # Check for large items first (most restrictive)
    for item in large_items:
        if item in text:
            return 'large'
    
    # Check for medium items
    for item in medium_items:
        if item in text:
            return 'medium'
    
    # Everything else is small (lamps, dishes, pillows, etc.)
    return 'small'

# Apply size classification to all requests
df["size_category"] = df["combined_items"].apply(classify_size)

# === Step 7: Flag request type (delivery vs pickup) ===
# Categorize requests to optimize truck routes (pickups first, then deliveries)
# This helps dashboard show different workflow categories
def label_request_type(text):
    """Determine if request is pickup (from donor) or delivery (to client)
    
    Args:
        text (str): Combined text describing the request
        
    Returns:
        str: 'pickup', 'delivery', or 'unspecified'
    """
    t = str(text).lower()
    if "pickup" in t or "pick up" in t:
        return "pickup"  # Collecting furniture from donor
    elif "deliver" in t or "delivery" in t:
        return "delivery"  # Delivering furniture to client
    return "unspecified"  # Will be treated as delivery by default

# Apply request type classification
df["request_type"] = df["combined_items"].apply(label_request_type)

# === Step 8: Save cleaned file ===
# Export processed data for use by routing and scheduling systems
clean_path = "data/tfp_clean_requests.csv"
df.to_csv(clean_path, index=False)
print("Cleaned data saved to:", clean_path)

# === Step 9: Summary ===
# Display data processing results for verification
print("\nSummary of size categories:")
print(df["size_category"].value_counts())

print("\nSummary of request types:")
print(df["request_type"].value_counts())

print("\nPreview of cleaned data:")
print(df.head(10))