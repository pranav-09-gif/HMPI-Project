"""
Generate realistic sample environmental monitoring datasets (CSV & Excel)
for testing the Heavy Metal Pollution Index (HMPI) application.
"""
import pandas as pd
import numpy as np

sites_data = [
    # Site Name, Latitude, Longitude, Pb, Cd, Cr, Ni, Zn, Cu, As, Fe
    # Category mix: Low (<50), Moderate (50-100), High (>100)
    # Pristine & upstream river sites (Low)
    {"Site_Name": "Site-01 (Upstream Spring)", "Latitude": 28.6139, "Longitude": 77.2090, "Pb": 0.002, "Cd": 0.0005, "Cr": 0.010, "Ni": 0.004, "Zn": 0.450, "Cu": 0.120, "As": 0.001, "Fe": 0.080},
    {"Site_Name": "Site-02 (Forest Catchment)", "Latitude": 28.6448, "Longitude": 77.2167, "Pb": 0.003, "Cd": 0.0008, "Cr": 0.012, "Ni": 0.005, "Zn": 0.520, "Cu": 0.140, "As": 0.002, "Fe": 0.095},
    {"Site_Name": "Site-03 (Highland Reservoir)", "Latitude": 28.5355, "Longitude": 77.2410, "Pb": 0.001, "Cd": 0.0003, "Cr": 0.008, "Ni": 0.003, "Zn": 0.310, "Cu": 0.090, "As": 0.001, "Fe": 0.050},
    {"Site_Name": "Site-04 (Protected Wetland A)", "Latitude": 28.5921, "Longitude": 77.0460, "Pb": 0.004, "Cd": 0.0010, "Cr": 0.015, "Ni": 0.006, "Zn": 0.600, "Cu": 0.180, "As": 0.002, "Fe": 0.110},
    {"Site_Name": "Site-05 (Rural Well North)", "Latitude": 28.7041, "Longitude": 77.1025, "Pb": 0.003, "Cd": 0.0007, "Cr": 0.018, "Ni": 0.007, "Zn": 0.750, "Cu": 0.210, "As": 0.003, "Fe": 0.130},
    {"Site_Name": "Site-06 (Suburban Lake Inflow)", "Latitude": 28.4595, "Longitude": 77.0266, "Pb": 0.004, "Cd": 0.0012, "Cr": 0.020, "Ni": 0.008, "Zn": 0.880, "Cu": 0.250, "As": 0.003, "Fe": 0.140},
    {"Site_Name": "Site-07 (Eco-Park Pond)", "Latitude": 28.5244, "Longitude": 77.1855, "Pb": 0.002, "Cd": 0.0006, "Cr": 0.011, "Ni": 0.005, "Zn": 0.400, "Cu": 0.110, "As": 0.001, "Fe": 0.070},
    {"Site_Name": "Site-08 (Agricultural Runoff E)", "Latitude": 28.6852, "Longitude": 77.3120, "Pb": 0.005, "Cd": 0.0014, "Cr": 0.022, "Ni": 0.009, "Zn": 1.100, "Cu": 0.320, "As": 0.004, "Fe": 0.160},
    
    # Moderate pollution sites (50 - 100)
    {"Site_Name": "Site-09 (Semi-Urban Canal)", "Latitude": 28.6280, "Longitude": 77.2789, "Pb": 0.007, "Cd": 0.0021, "Cr": 0.035, "Ni": 0.014, "Zn": 1.850, "Cu": 0.580, "As": 0.006, "Fe": 0.220},
    {"Site_Name": "Site-10 (Highway Intersection Drainage)", "Latitude": 28.5672, "Longitude": 77.1650, "Pb": 0.009, "Cd": 0.0025, "Cr": 0.042, "Ni": 0.017, "Zn": 2.200, "Cu": 0.720, "As": 0.007, "Fe": 0.260},
    {"Site_Name": "Site-11 (Municipal Drain Discharge)", "Latitude": 28.6692, "Longitude": 77.2315, "Pb": 0.008, "Cd": 0.0023, "Cr": 0.038, "Ni": 0.016, "Zn": 2.050, "Cu": 0.650, "As": 0.008, "Fe": 0.240},
    {"Site_Name": "Site-12 (Commercial Hub Outflow)", "Latitude": 28.6304, "Longitude": 77.2177, "Pb": 0.009, "Cd": 0.0027, "Cr": 0.045, "Ni": 0.018, "Zn": 2.450, "Cu": 0.810, "As": 0.007, "Fe": 0.270},
    {"Site_Name": "Site-13 (Railway Yard Sump)", "Latitude": 28.6600, "Longitude": 77.2250, "Pb": 0.010, "Cd": 0.0029, "Cr": 0.048, "Ni": 0.019, "Zn": 2.600, "Cu": 0.890, "As": 0.009, "Fe": 0.290},
    {"Site_Name": "Site-14 (Vehicular Depot Runoff)", "Latitude": 28.5800, "Longitude": 77.3100, "Pb": 0.008, "Cd": 0.0024, "Cr": 0.039, "Ni": 0.015, "Zn": 2.150, "Cu": 0.690, "As": 0.006, "Fe": 0.250},
    {"Site_Name": "Site-15 (Small Scale Foundry Outskirts)", "Latitude": 28.5100, "Longitude": 77.2800, "Pb": 0.009, "Cd": 0.0028, "Cr": 0.046, "Ni": 0.018, "Zn": 2.500, "Cu": 0.840, "As": 0.008, "Fe": 0.280},
    {"Site_Name": "Site-16 (Old Landfill Perimeter South)", "Latitude": 28.4800, "Longitude": 77.1500, "Pb": 0.010, "Cd": 0.0026, "Cr": 0.047, "Ni": 0.019, "Zn": 2.700, "Cu": 0.870, "As": 0.009, "Fe": 0.295},
    
    # High pollution hotspot sites (> 100)
    {"Site_Name": "Site-17 (Electroplating Cluster Outlet)", "Latitude": 28.7200, "Longitude": 77.1400, "Pb": 0.025, "Cd": 0.0085, "Cr": 0.120, "Ni": 0.055, "Zn": 6.800, "Cu": 2.900, "As": 0.024, "Fe": 0.720},
    {"Site_Name": "Site-18 (Battery Recycling Plant Drain)", "Latitude": 28.6900, "Longitude": 77.1200, "Pb": 0.042, "Cd": 0.0110, "Cr": 0.095, "Ni": 0.048, "Zn": 5.400, "Cu": 2.100, "As": 0.028, "Fe": 0.650},
    {"Site_Name": "Site-19 (Tannery Effluent Channel)", "Latitude": 28.7500, "Longitude": 77.2100, "Pb": 0.018, "Cd": 0.0062, "Cr": 0.190, "Ni": 0.040, "Zn": 4.900, "Cu": 1.950, "As": 0.021, "Fe": 0.580},
    {"Site_Name": "Site-20 (Heavy Industrial Estate East)", "Latitude": 28.6350, "Longitude": 77.3450, "Pb": 0.031, "Cd": 0.0098, "Cr": 0.145, "Ni": 0.062, "Zn": 7.500, "Cu": 3.400, "As": 0.032, "Fe": 0.810},
    {"Site_Name": "Site-21 (Chemical Park Creek)", "Latitude": 28.5600, "Longitude": 77.3600, "Pb": 0.022, "Cd": 0.0076, "Cr": 0.110, "Ni": 0.046, "Zn": 6.100, "Cu": 2.650, "As": 0.025, "Fe": 0.690},
    {"Site_Name": "Site-22 (Textile Dyeing Discharge)", "Latitude": 28.7100, "Longitude": 77.2800, "Pb": 0.019, "Cd": 0.0058, "Cr": 0.135, "Ni": 0.038, "Zn": 5.200, "Cu": 2.400, "As": 0.019, "Fe": 0.610},
    {"Site_Name": "Site-23 (Metal Smelter Slag Runoff)", "Latitude": 28.7800, "Longitude": 77.1600, "Pb": 0.038, "Cd": 0.0125, "Cr": 0.160, "Ni": 0.070, "Zn": 8.900, "Cu": 3.800, "As": 0.036, "Fe": 0.950},
    {"Site_Name": "Site-24 (E-Waste Processing Site)", "Latitude": 28.6750, "Longitude": 77.0850, "Pb": 0.035, "Cd": 0.0105, "Cr": 0.130, "Ni": 0.065, "Zn": 7.200, "Cu": 3.600, "As": 0.030, "Fe": 0.840},
    {"Site_Name": "Site-25 (Industrial Harbor Sump)", "Latitude": 28.5400, "Longitude": 77.2600, "Pb": 0.027, "Cd": 0.0080, "Cr": 0.105, "Ni": 0.052, "Zn": 6.300, "Cu": 2.750, "As": 0.022, "Fe": 0.710},
]

df = pd.DataFrame(sites_data)
df.to_csv("sample_data.csv", index=False)
df.to_excel("sample_data.xlsx", index=False)
print(f"Generated sample_data.csv and sample_data.xlsx with {len(df)} monitoring sites.")
