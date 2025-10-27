# Phase 2 Prototype for The Furniture Project
# Using mock data to simulate clustering + route optimization

import numpy as np
from sklearn.cluster import KMeans
import pyswarms as ps
from geopy.distance import great_circle


# STEP 1: Simulated daily requests
# Each request = (latitude, longitude, item size category)
np.random.seed(42)
coords = np.random.uniform([41.2, -96.1], [41.4, -95.9], (10, 2))
sizes = np.random.choice(['small', 'medium', 'large'], 10)

print("Sample requests (location + size):\n")
for i, (lat, lon, s) in enumerate(zip(coords[:,0], coords[:,1], sizes)):
    print(f"Request {i+1}: ({lat:.3f}, {lon:.3f}) - {s}")


# STEP 2: Stage 1 - Geographic Clustering
kmeans = KMeans(n_clusters=2, random_state=0)
zones = kmeans.fit_predict(coords)

print("\nStage 1: Cluster assignments")
for i, zone in enumerate(zones):
    print(f"Request {i+1} assigned to Zone {zone}")


# STEP 3: Stage 2 - Route Optimization (using PSO)
# Focus on one zone for demo
warehouse = np.array([41.3, -96.0])  # Example warehouse location
zone_coords = coords[zones == 0]
zone_coords = np.vstack([warehouse, zone_coords, warehouse])  # Add warehouse at start and end
n = len(zone_coords)

def route_distance(order):
    total = 0
    for i in range(n - 1):
        total += great_circle(zone_coords[int(order[i])], zone_coords[int(order[i + 1])]).miles
    return total

# Fitness function for PSO: minimize total travel distance
def fitness_function(x):
    return np.array([route_distance(route.argsort()) for route in x])

# PySwarms configuration
options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}
optimizer = ps.single.GlobalBestPSO(n_particles=30, dimensions=n, options=options)

best_cost, best_pos = optimizer.optimize(fitness_function, iters=50)

print("\nStage 2: Optimized route results")
print("Best route order:", best_pos.argsort())
print("Shortest distance:", round(best_cost, 2), "miles")

import csv

# After optimization
output = {
    "zone_0": {
        "truck": 1,
        "route_order": best_pos.argsort().tolist(),
        "total_distance_miles": round(best_cost, 2)
    }
}

# Write to CSV
with open("routes_output.csv", "w", newline='') as f:
    writer = csv.writer(f)
    
    # Write header
    writer.writerow(["zone", "truck", "route_order", "total_distance_miles"])
    
    # Write data
    writer.writerow([
        "zone_0",
        output["zone_0"]["truck"],
        ",".join(map(str, output["zone_0"]["route_order"])),
        output["zone_0"]["total_distance_miles"]
    ])

