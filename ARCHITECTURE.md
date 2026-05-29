# Bus Charging Scheduler - Architecture & Design

## 1. The Framework Choice: Constraint Programming (OR-Tools)
To solve the scheduling problem, I utilized **Google OR-Tools (CP-SAT Solver)** instead of traditional heuristic loops or greedy algorithms.
* **Why it's the right fit:** Scheduling buses across limited charging resources is a classic Constraint Satisfaction Problem (CSP). Using a constraint solver allows the engine to evaluate the entire timeline globally rather than making suboptimal local decisions. It guarantees a mathematically optimal (or feasible) schedule without hardcoding complex `if/else` collision logic. The `AddNoOverlap` constraint perfectly handles the 1-charger bottleneck.

## 2. Data Structure Design
I strictly separated the business logic from the data state. A "Scenario" is not just a list of buses; it is a full representation of the universe for that specific simulation, encoded in JSON.
* The JSON schema (`models.py`) encapsulates the route distances, battery limits, charger counts, and the bus fleet.
* The Python engine dynamically constructs the highway and variables strictly based on the JSON file.

## 3. Anticipating Future Changes
By designing a data-driven structure, the system handles real-world scaling gracefully:
* **Change segment distance or add a new station (e.g., Station E):** Simply update the `routes` array in the JSON. The travel time helper function dynamically recalculates distances. No Python code changes required.
* **Double the chargers at Station B:** Update `"charg": 2` in the JSON. (The solver would just need a minor loop update to apply `AddNoOverlap` per charger capacity, but the data structure is already prepared for it).
* **Swap in a new operator:** Just change the `"Oper"` string in the JSON.
* **Change battery capacity:** Update `"battery_range"` in the JSON.

## 4. Modifying Weights & Adding Rules
* **Changing a weight:** Weights are exposed at the top of every scenario JSON file. An operations engineer can tweak `"operator": 2.0` in the JSON without ever opening the Python repository.
* **Adding a new rule:** Because we use CP-SAT, adding a rule like "KPN buses have priority" does not require rewriting the core engine. You simply add a new boolean constraint to the model before calling `solver.Solve()` (e.g., heavily penalizing wait times specifically for variables tied to the KPN operator string).