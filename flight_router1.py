# Step 1 --- Graph Builder ---
import csv
import networkx as nx

# Output path
output_path = r"C:\Users\npetr\Documents\Utopia\route_results.csv"

# Global Results Storage
all_results = []

# Time expressed in hours and minutes
def minutes_to_hhmm(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"

# CSV formatting helper
def format_result_for_csv(result):
    return{
        "origin": result["route"][0],
        "destination": result["route"][-1],
        "route": " -> ".join(result["route"]),
        "connections": result["connections"],
        "total_duration_min": result["total_duration"],
        "total_duration_hhmm": minutes_to_hhmm(result["total_duration"]),
        "leg_durations_min": " | ".join(
            str(d) for d in result["leg_durations"]
        ),
        "leg_durations_hhmm": " | ".join(
            minutes_to_hhmm(d) for d in result["leg_durations"]
        ),
        "airlines": " | ".join(result["airlines"]),
        "aircraft": " | ".join(result["aircrafts"]),
        "flight_numbers": " | ".join(result["flight_numbers"])
    }

import io
import csv

#define exporting
def export_results_to_csv(results):
    """
    Takes a list of route result dicts and returns CSV text.
    This is the single source of truth for CSV structure.
    """
    if not results:
        return None
    
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

    return output.getvalue()

#define building the flight graph
def build_flight_graph(csv_path):
    G = nx.DiGraph()

    with open(csv_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            origin = row["from"].strip()
            destination = row["to"].strip()

            try:
                duration = int(row["duration"].strip())
            except ValueError:
                continue

            airline = str(row.get("airline", "")).strip()
            aircraft = str(row.get("aircraft", "")).strip()
            flight_number = row.get("flight number")
            if flight_number is None:
                flight_number = ""
            flight_number = str(flight_number).strip()

            G.add_edge(
                origin,
                destination,
                duration=duration,
                airline=airline,
                aircraft=aircraft,
                flight_number=flight_number
            )

    return G

#define airport name mapping
def load_airport_names(csv_path):
    airport_map = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row["ICAO code"].strip()
            name = row["airport name"].strip()
            airport_map[icao] = name
    return airport_map

# Step 2 --- Reusable Routing Function ---
def best_route(G, origin, destination):
    try:
        candidate_paths = list(nx.all_shortest_paths(G, source=origin, target=destination))

        if not candidate_paths:
            return None

        best_path = None
        best_time = float("inf")

        for path in candidate_paths:
            total_time = sum(
                G[u][v]["duration"] for u, v in zip(path[:-1], path[1:])
            )

            if total_time < best_time:
                best_time = total_time
                best_path = path

        if best_path is None:
            return None

        airlines = []
        aircrafts = []
        leg_durations = []
        flight_numbers = []

        for u, v in zip(best_path[:-1], best_path[1:]):
            edge = G[u][v]
            duration = edge["duration"]
            leg_durations.append(duration)
            airlines.append(edge["airline"])
            aircrafts.append(edge["aircraft"])
            flight_numbers.append(edge["flight_number"])

        return {
            "route": best_path,
            "connections": len(best_path) - 1,
            "total_duration": best_time,
            "leg_durations": leg_durations,
            "airlines": airlines,
            "aircrafts": aircrafts,
            "flight_numbers": flight_numbers
        }

    except nx.NetworkXNoPath:
        return None
    
# Step 3 --- Application Entry Point ---
if __name__ == "__main__":
    G = build_flight_graph("flights.csv")
    airport_map = load_airport_names("airports.csv")
    print(f"Loaded {G.number_of_nodes()} airports and {G.number_of_edges()} flights")

def run_cli():
    while True:
        origin = input("\nEnter origin airport (or 'q' to quit): ").strip()
        if origin.lower() == "q":
            break

        destination = input("Enter destination airport: ").strip()

        result = best_route(G, origin, destination)

        for icao in result["route"]:
            name = airport_map.get(icao, "Unkown Airport")
            print(f"{icao} ({name})")

        if result:
            print("\nRoute:", " -> ".join(result["route"]))
            print("Connections:", result["connections"])
            print("Airlines:", " -> ".join(result["airlines"]))
            print("Aircraft:", " -> ".join(result["aircrafts"]))
            print("Total Duration (min):", result["total_duration"])
            print("Leg Durations (min):", " -> ".join(str(d) for d in result["leg_durations"]))
            print("Flight Numbers:", " -> ".join(result["flight_numbers"]))

            # Store for CSV export
            all_results.append(format_result_for_csv(result))
        else:
            print("No route found")

# -----------------------------
# Step 4: Export all results to CSV
# -----------------------------
    if all_results:
        csv_text = export_results_to_csv(all_results)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            f.write(csv_text)

        print(f"\nExported {len(all_results)} routes to {output_path}")
    else:
        print("\nNo routes to export.")

if __name__ == "__main__":
    run_cli()