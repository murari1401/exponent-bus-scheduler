import json
from ortools.sat.python import cp_model
from models import Scenario, R, Bus, s

def load_scenario(filepath: str) -> Scenario:
    with open(filepath, 'r') as f:
        data = json.load(f)

    stations = [s(**p) for p in data["routes"]["sta_s"]]
    route = R(
        sta_s=stations, battery_range=data["routes"]["battery_range"],
        charge_time=data["routes"]["charge_time"], speed_p_min=data["routes"]["speed_p_min"]
    )
    buses = [Bus(**b) for b in data["buses"]]
    return Scenario(Scenario_name=data["Scenario_name"], weights=data["weights"], routes=route, buses=buses)

def solve_schedule(scenario: Scenario):
    model = cp_model.CpModel()

    station_intervals = {"A": [], "B": [], "C": [], "D": []}
    all_end_times = []
    bus_tracking = {}

    def travel_time(loc1, loc2):
        d1 = next(st.dist_from_start for st in scenario.routes.sta_s if st.name == loc1)
        d2 = next(st.dist_from_start for st in scenario.routes.sta_s if st.name == loc2)
        return int(abs(d2 - d1) / scenario.routes.speed_p_min)

    for bus in scenario.buses:
        bus_tracking[bus.bus_id] = []

        if bus.Direction == "Bengaluru_Kochi":
            path = ["Bengaluru", "A", "B", "C", "D", "Kochi"]
        else:
            path = ["Kochi", "D", "C", "B", "A", "Bengaluru"]

        charges = {st: model.NewBoolVar(f"charge_{bus.bus_id}_{st}") for st in ["A", "B", "C", "D"]}
        model.Add(charges["A"] + charges["B"] >= 1)
        model.Add(charges["B"] + charges["C"] >= 1)
        model.Add(charges["C"] + charges["D"] >= 1)

        current_time_var = bus.Depart_time

        for i in range(1, len(path)):
            prev_station = path[i-1]
            curr_station = path[i]
            drive_time = travel_time(prev_station, curr_station)

            arrival = model.NewIntVar(0, 10000, f"arr_{bus.bus_id}_{curr_station}")
            model.Add(arrival == current_time_var + drive_time)

            if curr_station in ["A", "B", "C", "D"]:
                wait = model.NewIntVar(0, 1000, f"wait_{bus.bus_id}_{curr_station}")
                model.Add(wait == 0).OnlyEnforceIf(charges[curr_station].Not())

                start_charge = model.NewIntVar(0, 10000, f"schg_{bus.bus_id}_{curr_station}")
                model.Add(start_charge == arrival + wait)

                end_charge = model.NewIntVar(0, 10000, f"echg_{bus.bus_id}_{curr_station}")
                model.Add(end_charge == start_charge + scenario.routes.charge_time)

                depart = model.NewIntVar(0, 10000, f"dep_{bus.bus_id}_{curr_station}")
                model.Add(depart == end_charge).OnlyEnforceIf(charges[curr_station])
                model.Add(depart == arrival).OnlyEnforceIf(charges[curr_station].Not())

                interval = model.NewOptionalIntervalVar(
                    start_charge, scenario.routes.charge_time, end_charge,
                    charges[curr_station], f"int_{bus.bus_id}_{curr_station}"
                )
                station_intervals[curr_station].append(interval)
                current_time_var = depart

                bus_tracking[bus.bus_id].append({
                    "station": curr_station, "arrival": arrival, "wait": wait,
                    "depart": depart, "is_charging": charges[curr_station]
                })
            else:
                all_end_times.append(arrival)
                bus_tracking[bus.bus_id].append({"station": curr_station, "arrival": arrival})

    for station_name in ["A", "B", "C", "D"]:
        model.AddNoOverlap(station_intervals[station_name])

    model.Minimize(sum(all_end_times))
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        final_timeline = []
        for bus_id, events in bus_tracking.items():
            for event in events:
                if event["station"] in ["A", "B", "C", "D"]:
                    final_timeline.append({
                        "Bus": bus_id,
                        "Station": event["station"],
                        "Arrival": str(solver.Value(event["arrival"])),
                        "Wait Time": str(solver.Value(event["wait"])),
                        "Charged?": "Yes" if solver.Value(event["is_charging"]) == 1 else "No",
                        "Departure": str(solver.Value(event["depart"]))
                    })
                else:
                    final_timeline.append({
                        "Bus": bus_id,
                        "Station": event["station"],
                        "Arrival": str(solver.Value(event["arrival"])),
                        "Wait Time": "-",
                        "Charged?": "-",
                        "Departure": "-"
                    })
        return final_timeline
    else:
        return None