import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- Helper function to format time values ---
def format_time(time_val):
    """Converts float time (e.g., 7.5) to a string format (e.g., '07:30')."""
    if pd.isna(time_val):
        return ""
    try:
        hours = int(time_val)
        minutes = int((time_val * 100) % 100)
        return f"{hours:02d}:{minutes:02d}"
    except (ValueError, TypeError):
        return "" # Return empty for non-numeric values

# --- DATA LOADING AND CLEANING ---
try:
    df = pd.read_excel("bus_data.xlsx", skiprows=4)
    
    df.rename(columns={
        df.columns[0]: 'Route No',
        df.columns[1]: 'Stop Name',
        df.columns[2]: 'Stop Name Tamil',
        df.columns[7]: 'Bus Fee',
        df.columns[8]: 'Time',
        df.columns[9]: 'RouteMapURL'
    }, inplace=True)
    
    df['Route No'] = pd.to_numeric(df['Route No'], errors='coerce')
    df.dropna(subset=['Route No', 'Stop Name'], inplace=True)
    df['Route No'] = df['Route No'].astype(int)

    # --- NEW: Pre-format the data for better display ---
    df['Time'] = df['Time'].apply(format_time)
    # Format Bus Fee with commas
    df['Bus Fee'] = df['Bus Fee'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")

except FileNotFoundError:
    print("Error: 'bus_data.xlsx' not found.")
    df = pd.DataFrame()

# --- WEB PAGE ROUTES ---
@app.route("/")
def home():
    if not df.empty:
        stop_names = sorted(df['Stop Name'].dropna().unique())
        all_routes = sorted(df['Route No'].unique())
    else:
        stop_names, all_routes = [], []
    return render_template("index.html", stop_names=stop_names, all_routes=all_routes)

@app.route("/search")
def search():
    query = request.args.get('stop_name')
    if query:
        return redirect(url_for('show_stop_info', stop_name=query))
    return redirect(url_for('home'))

@app.route("/stop/<string:stop_name>")
def show_stop_info(stop_name):
    matching_routes_df = df[df['Stop Name'].str.lower() == stop_name.lower()]
    route_numbers = sorted(matching_routes_df['Route No'].unique())
    
    if not route_numbers:
        return f"<h2>No routes found for stop: {stop_name}</h2>"
        
    all_routes_data = []
    for route_no in route_numbers:
        route_df = df[df['Route No'] == route_no]
        if not route_df.empty:
            map_url = route_df['RouteMapURL'].iloc[0] if 'RouteMapURL' in route_df.columns else None
            
            # Now includes the pre-formatted Time and Bus Fee
            stops_for_chart = route_df[['Stop Name', 'Stop Name Tamil', 'Bus Fee', 'Time']].to_dict(orient='records')

            all_routes_data.append({
                "route_no": route_no,
                "map_url": map_url,
                "stops": stops_for_chart
            })
            
    return render_template("stop_info.html", stop_name=stop_name, routes_data=all_routes_data)

@app.route("/route/<int:route_no>")
def show_route(route_no):
    route_df = df[df['Route No'] == route_no]
    if not route_df.empty:
        first_stop = route_df['Stop Name'].iloc[0]
        return redirect(url_for('show_stop_info', stop_name=first_stop))
    return f"<h2>No data found for Route {route_no}</h2>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

