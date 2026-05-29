import streamlit as st
import pandas as pd
from scheduler import load_scenario, solve_schedule
import os

st.set_page_config(page_title="Bus Charging Scheduler", layout="wide")
st.title("⚡ Electric Bus Charging Scheduler")

scenario_choice = st.selectbox(
    "Choose a Scenario to run:",
    [
        "Scenario 1 - Even spacing",
        "Scenario 2 - Bunched start",
        "Scenario 3 - Asymmetric load",
        "Scenario 4 - Operator-heavy",
        "Scenario 5 - Worst case convergence"
    ]
)

scenario_files = {
    "Scenario 1 - Even spacing": "data/scenario_1.json",
    "Scenario 2 - Bunched start": "data/scenario_2.json",
    "Scenario 3 - Asymmetric load": "data/scenario_3.json",
    "Scenario 4 - Operator-heavy": "data/scenario_4.json",
    "Scenario 5 - Worst case convergence": "data/scenario_5.json"
}

file_path = scenario_files[scenario_choice]

if os.path.exists(file_path):
    scenario_data = load_scenario(file_path)

    st.subheader(f"Raw Input: {scenario_data.Scenario_name}")
    input_df = pd.DataFrame([vars(b) for b in scenario_data.buses])
    st.dataframe(input_df, width='stretch')

    st.divider()

    with st.spinner("Calculating the perfect schedule..."):
        results = solve_schedule(scenario_data)

    if results:
        st.success("Schedule calculated successfully!")
        results_df = pd.DataFrame(results)

        st.subheader("🚌 Per-Bus Timetable")
        st.dataframe(results_df, width='stretch')

        st.subheader("🚉 Per-Station Charging Queue")
        charged_df = results_df[results_df["Charged?"] == "Yes"].copy()
        charged_df["Arrival_Num"] = pd.to_numeric(charged_df["Arrival"])

        cols = st.columns(4)
        for idx, station in enumerate(["A", "B", "C", "D"]):
            with cols[idx]:
                st.markdown(f"**Station {station}**")
                station_queue = charged_df[charged_df["Station"] == station].sort_values("Arrival_Num")
                if not station_queue.empty:
                    st.dataframe(station_queue[["Bus", "Arrival", "Wait Time"]], hide_index=True, width='stretch')
                else:
                    st.caption("No buses charged here.")
    else:
        st.error("Could not find a valid schedule.")
else:
    st.warning("Data file not found. Please ensure JSON files are inside the 'data' folder.")