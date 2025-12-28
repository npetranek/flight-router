import streamlit as st
from flight_router1 import build_flight_graph, best_route, minutes_to_hhmm, load_airport_names

if "ended" not in st.session_state:
    st.session_state.ended = False

# Page setup
st.set_page_config(page_title="Flight Route Finder", layout="centered")
st.title("✈️ Flight Route Finder")
if st.session_state.get("ended", False):
    st.title("Session Ended")
    st.info("This session has been closed. Please refresh the page to start a new one.")
    st.stop()

#load airport names once
@st.cache_resource
def get_airport_map():
    return load_airport_names("airports.csv")

airport_map = get_airport_map()

# Load graph ONCE
@st.cache_resource
def load_graph():
    return build_flight_graph("flights.csv")

G = load_graph()

def reset_search():
    for key in["origin", "destination"]:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.stops = []

# MULTI STOP UI STATE
if "stops" not in st.session_state:
    st.session_state.stops = [] #no stops until user adds

# User inputs
origin = st.text_input(
    "Origin Airport Code",
    key="origin"
    ).upper()

#add stop button
st.subheader("Stops (Optional)")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Add Stop"):
        st.session_state.stops.append("")

#remove stop button
with col2:
    if st.button("Remove Stop"):
        if st.session_state.stops:
            st.session_state.stops.pop()

#render stop boxes
for i in range(len(st.session_state.stops)):
    st.session_state.stops[i] = st.text_input(
        f"Stop {i+1}",
        value=st.session_state.stops[i]
    ).upper()

destination = st.text_input(
    "Destination Airport Code",
    key="destination"
    ).upper()

colA, colB, colC = st.columns(3)
with colB:
    if st.button("New Search"):
        reset_search()
        st.rerun()

with colC:
    if st.button("End Session"):
        st.session_state.clear()
        st.session_state.ended = True
        st.rerun()

# Run routing
with colA:
    run_search = st.button("Find Best Route")
        
if run_search:    
    # Collect airport sequence
    airports = [origin] + [s for s in st.session_state.stops if s] + [destination]

    if any(a == "" for a in airports):
        st.warning("Please fill all airport fields.")
    else:
        full_route = []
        full_airlines = []
        full_aircraft = []
        full_leg_durations = []
        full_flight_numbers = []

        total_minutes = 0
        total_connections = 0

        # Each segment: A→B, B→C, etc.
        valid = True
        for a, b in zip(airports[:-1], airports[1:]):
            segment = best_route(G, a, b)
            if not segment:
                st.error(f"No route found between {a} and {b}.")
                valid = False
                break

            # Build combined full route
            if not full_route:
                full_route.extend(segment["route"])
            else:
                full_route.extend(segment["route"][1:])  # skip duplicate node

            full_airlines.extend(segment["airlines"])
            full_aircraft.extend(segment["aircrafts"])
            full_leg_durations.extend(segment["leg_durations"])
            full_flight_numbers.extend(segment["flight_numbers"])

            total_minutes += segment["total_duration"]
            total_connections += segment["connections"]

        if valid:
            import pandas as pd

            #convert ICAO codes to airport names using airport_map
            full_route_display = [f"{code} ({airport_map.get(code, 'Unkown Airport')})" for code in full_route]

            #build per-leg table
            legs = []
            for i in range(len(full_route) - 1):
                legs.append({
                    "Leg": i + 1,
                    "From": full_route_display[i],
                    "To": full_route_display[i + 1],
                    "Airline": full_airlines[i],
                    "Aircraft": full_aircraft[i],
                    "Flight Numbers": full_flight_numbers[i],
                    "Duration": minutes_to_hhmm(full_leg_durations[i])
                })

            df = pd.DataFrame(legs)

            #display summary above the table
            st.markdown("### Summary")
            st.write(f"**Connections:** {total_connections}")
            st.write(f"**Total Duration:** {minutes_to_hhmm(total_minutes)}")

            #display the table
            st.markdown("### Route Details")
            st.dataframe(df, use_container_width=True)

            

            st.write("To export generated table to CSV - hover mouse over table then click the download icon in the top right corner.")