import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from counterlift.artifacts import verify_run

st.set_page_config(page_title="CounterLift", page_icon="📈", layout="wide")
st.title("CounterLift")
st.caption("Offline evidence for marketing allocation decisions")
run_path = Path(os.environ.get("COUNTERLIFT_RUN", "runs/demo"))
if not (run_path / "manifest.json").exists():
    st.info("Generate a run first: counterlift demo --out runs/demo")
    st.stop()
try:
    manifest = verify_run(run_path, public=True)
except (ValueError, OSError, KeyError) as error:
    st.error(f"Run is incomplete or failed integrity verification: {error}")
    st.stop()
experiment = json.loads((run_path / "experiment.json").read_text())
evaluation = pd.read_csv(run_path / "policy_evaluation.csv")
st.info(f"Dataset: {manifest['provenance']['dataset']}")
if not manifest["provenance"].get("not_criteo", False):
    st.warning("Publisher nonuniform subsampling may affect causal identification. Released-sample randomization is an assumption, not verified by a checksum or balance check.")
st.caption("Financial values are assumptions. All effects are offline estimates. No live campaign has been run.")
summary, allocation, models, audit = st.tabs(["Experiment health", "Budget simulator", "Policy evidence", "Run audit"])
with summary:
    a, b, c = st.columns(3)
    a.metric("Analyzed records", f"{experiment['n']:,}")
    b.metric("Conversion effect", f"{100 * experiment['ate']:.4f} percentage points")
    c.metric("Treatment allocation", f"{experiment['treatment_rate']:.1%}")
    st.write(f"95% interval: [{100*experiment['lower']:.4f}, {100*experiment['upper']:.4f}] percentage points")
    st.bar_chart(pd.Series(experiment["standardized_mean_differences"], name="Standardized mean difference"))
    st.write(experiment["srm_note"])
    st.write("SRM p-value:", experiment["srm_pvalue"])
with allocation:
    st.write("Validated policy:", manifest["winner"])
    st.caption("Budget exploration is exploratory; only the predeclared selection budget is confirmatory. Model and profitability threshold were chosen before test evaluation. Changing financial assumptions below revalues this fixed allocation; retrain for a new optimized threshold.")
    population = st.number_input("Eligible population (representativeness assumed)", 100, 10_000_000, 100_000)
    fraction = st.select_slider("Maximum target fraction", options=sorted(evaluation.budget_fraction.unique()), value=min(evaluation.budget_fraction.unique(), key=lambda b: abs(b-manifest["selection_budget"])))
    unit_cost = st.number_input("Assumed cost per assignment", 0., 100., float(manifest["cost_per_assignment"]), .01)
    conversion_value = st.number_input("Assumed value per conversion", .01, 10000., max(.01, float(manifest["value_per_conversion"])), 1.)
    row = evaluation[(evaluation.model == manifest["winner"]) & np.isclose(evaluation.budget_fraction, fraction)].iloc[0]
    selected = population * row.selected_fraction
    a, b, c = st.columns(3)
    a.metric("Expected incremental conversions", f"{population * row.incremental_per_user:,.1f}")
    b.metric("Assumed spend", f"{selected * unit_cost:,.2f}")
    c.metric("Scenario incremental net value", f"{population * row.incremental_per_user * conversion_value-selected*unit_cost:,.2f}")
    st.write(f"Fixed-policy conversion interval: [{population*row.lower:,.1f}, {population*row.upper:,.1f}]")
    st.caption("Interval excludes refitting and model-selection uncertainty. Budget curves have pointwise, not simultaneous, intervals.")
    display = evaluation[np.isclose(evaluation.budget_fraction, fraction)].copy()
    display["scenario_net_value"] = population * (display.incremental_per_user * conversion_value-display.selected_fraction * unit_cost)
    st.dataframe(display[["model", "selected_fraction", "scenario_net_value", "incremental_per_user", "lower", "upper"]], hide_index=True)
with models:
    st.line_chart(evaluation.pivot(index="budget_fraction", columns="model", values="incremental_per_user"))
    st.dataframe(evaluation, hide_index=True)
    st.write("Paired test comparison at the predeclared selection budget:")
    st.json(manifest["test_net_difference_vs_response_at_selection_budget"])
    comparison = manifest["test_net_difference_vs_response_at_selection_budget"]
    if comparison["upper"] < 0:
        st.warning("The selected policy underperformed response targeting in this fixed-policy test comparison.")
    elif comparison["lower"] <= 0:
        st.warning("The fixed-policy comparison is inconclusive: its interval includes zero.")
    else:
        st.info("The fixed-policy interval favors the selected policy; this excludes learning and selection uncertainty and is not deployment approval.")
    st.download_button("Download policy evaluation", evaluation.to_csv(index=False), "policy_evaluation.csv")
with audit:
    st.json(manifest)
    st.write("Features f0–f11 are anonymized. No demographic, channel, timestamp or product meanings are inferred.")
