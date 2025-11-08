from __future__ import annotations

import os
import sys
import json
from uuid import uuid4
import streamlit as st
import pandas as pd

# Ensure `src/` is importable when running locally (Docker sets PYTHONPATH already)
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
	sys.path.insert(0, _SRC)

from solar.energy.devices import Device, DeviceList
from solar.energy.calculator import compute_energy_summaries
from state.persistence import load_devices, save_devices
from solar.cables.awg_table import AWG_SIZES, AWG_AREA_MM2
from solar.cables.ampacity import BASE_AMPACITY_CU_THHN_30C, temp_correction_factor
from solar.cables.sizing import resistivity_ohm_m

st.set_page_config(page_title="Solar Planner", page_icon="☀️", layout="wide")

st.title("☀️ Solar Planner")
st.caption("All-in-one: Consumption, Cable Sizing, and Parts List")


def _init_state():
	if "devices" not in st.session_state:
		try:
			loaded = [Device(**d) for d in load_devices()]
		except Exception:
			loaded = []
		st.session_state.devices = loaded


def _persist():
	save_devices([d.model_dump() for d in st.session_state.devices])


_init_state()

tab1, tab2, tab3 = st.tabs(["Consumption", "Cable Sizing", "Parts List"])

with tab1:
	st.subheader("Energy Consumption Calculator")
	# Import/Export controls
	imp_col1, imp_col2, imp_col3 = st.columns([3, 2, 2])
	with imp_col1:
		uploaded = st.file_uploader("Import JSON (list or {devices: [...]})", type=["json"], accept_multiple_files=False)
	with imp_col2:
		import_mode = st.radio("Import Mode", ["Append", "Replace"], horizontal=True)
	with imp_col3:
		if st.button("Import") and uploaded is not None:
			try:
				payload = json.loads(uploaded.read())
				if isinstance(payload, dict) and "devices" in payload:
					rows = payload["devices"]
				elif isinstance(payload, list):
					rows = payload
				else:
					raise ValueError("Unsupported JSON shape. Expect a list or {devices: [...]}.")
				new_devices = []
				for row in rows:
					norm = {
						"id": row.get("id", str(uuid4())),
						"name": row.get("name", "Unnamed"),
						"power_w": float(row.get("power_w", row.get("power", 0))),
						"duty_hours_per_day": float(row.get("duty_hours_per_day", row.get("duty", 0))),
						"count": int(row.get("count", 1)),
					}
					new_devices.append(Device(**norm))
				if import_mode == "Replace":
					st.session_state.devices = new_devices
				else:
					st.session_state.devices.extend(new_devices)
				_persist()
				st.success(f"Imported {len(new_devices)} devices ({import_mode.lower()}).")
				st.experimental_rerun()
			except Exception as e:
				st.error(f"Import failed: {e}")
	with st.form("add_device_form", clear_on_submit=True):
		cols = st.columns([3, 2, 2, 2])
		name = cols[0].text_input("Device name", help="A short name for the device, e.g. 'washing machine'")
		power = cols[1].number_input("Power (W)", min_value=0.0, step=10.0, help="Typical power draw in watts while operating")
		duty = cols[2].number_input("Duty (h/day)", min_value=0.0, max_value=24.0, step=0.5, help="Average hours per day the device is on")
		count = cols[3].number_input("Quantity", min_value=0, step=1, value=1, help="How many of this device you use")
		submitted = st.form_submit_button("Add device")
		if submitted:
			try:
				device = Device(name=name, power_w=power, duty_hours_per_day=duty, count=count)
				st.session_state.devices.append(device)
				_persist()
				st.success(f"Added {device.name}")
			except Exception as e:
				st.error(f"Invalid input: {e}")

	st.markdown("### Devices")
	if not st.session_state.devices:
		st.info("No devices yet. Add your first device above.")
	else:
		for d in list(st.session_state.devices):
			cols = st.columns([4, 2, 2, 2, 2])
			cols[0].markdown(f"**{d.name}**")
			cols[1].markdown(f"{d.power_w:.0f} W")
			cols[2].markdown(f"{d.duty_hours_per_day:.1f} h/d")
			cols[3].markdown(f"x{d.count}")
			wh = d.daily_wh
			cols[4].markdown(f"{wh:.0f} Wh/d")

			remove = cols[0].button("Remove", key=f"rm_{d.id}")
			if remove:
				st.session_state.devices = [x for x in st.session_state.devices if x.id != d.id]
				_persist()
				st.experimental_rerun()

	device_list = DeviceList(devices=st.session_state.devices)
	summary = compute_energy_summaries(device_list)

	st.divider()
	st.subheader("Totals")
	c1, c2 = st.columns(2)
	c1.metric("Daily energy", f"{summary['total_kwh_per_day']:.2f} kWh/day")
	c2.metric("Average power", f"{summary['avg_power_w']:.0f} W")

	export_col1, export_col2 = st.columns([1,3])
	with export_col1:
		st.download_button(
			label="Download devices.json",
			data=json.dumps([d.model_dump() for d in st.session_state.devices], indent=2),
			file_name="devices.json",
			mime="application/json",
		)
	st.caption("NOTE: Click 'download devices.json' to save your device list if you don't want to lose it")

with tab2:
	st.subheader("Cable Sizing")
	with st.form("cable_form"):
		c1, c2, c3 = st.columns(3)
		install_type = c1.selectbox("Installation Type", ["DC", "AC_1PH", "AC_3PH"], index=0, help="Type of circuit: DC, single-phase AC, or three-phase AC")
		voltage_v = c2.number_input("System Voltage (V)", min_value=1.0, value=24.0, help="Nominal circuit voltage (e.g., 12/24/48V DC or 120/230/400V AC)")
		load_w = c3.number_input("Load (W)", min_value=1.0, value=500.0, help="Maximum expected power on this run")
		c4, c5, c6 = st.columns(3)
		distance_m = c4.number_input("One-way Distance (m)", min_value=0.1, value=10.0, help="Physical one-way length from source to load in meters")
		drop_pct = c5.number_input("Allowable Voltage Drop (%)", min_value=0.1, max_value=10.0, value=3.0, help="Max percentage voltage drop you allow on this circuit")
		material = c6.selectbox("Conductor Material", ["Cu", "Al"], index=0, help="Copper (Cu) or Aluminum (Al) conductor")
		c7, c8, c9 = st.columns(3)
		ambient = c7.number_input("Ambient Temp (°C)", min_value=-20.0, max_value=80.0, value=30.0, help="Average ambient temperature for the cable run")
		pf = c8.number_input("Power Factor (AC)", min_value=0.1, max_value=1.0, value=1.0, help="Power factor for AC loads (use 1.0 for DC)")
		eff = c9.number_input("Efficiency", min_value=0.5, max_value=1.0, value=1.0, help="Additional efficiency factor (e.g., inverter/controller efficiency)")
		ocpd_a = st.number_input("OCPD rating (A) for grounding", min_value=0.0, value=0.0, help="Optional: Overcurrent protection device rating used to suggest grounding conductor size")
		submitted = st.form_submit_button("Calculate")
		if submitted:
			try:
				from solar.cables.sizing import CableInputs, size_cable

				result = size_cable(
					CableInputs(
						install_type=install_type, distance_m=distance_m, load_w=load_w, voltage_v=voltage_v,
						drop_pct=drop_pct, material=material, ambient_c=ambient, power_factor=pf, efficiency=eff,
						ocpd_a=(ocpd_a or None),
					)
				)
				st.success("Cable sizing computed successfully.")
				r1, r2, r3 = st.columns(3)
				r1.metric("Minimum AWG", result.awg)
				r2.metric("Voltage drop", f"{result.drop_pct:.2f}%")
				r3.metric("Load current", f"{result.current_a:.1f} A")

				# Build results table across sizes
				def _path_factor(itype: str) -> float:
					return (3 ** 0.5) if itype == "AC_3PH" else 2.0

				def _current_a(load_w: float, V: float, PF: float, effi: float, itype: str) -> float:
					den = (3 ** 0.5) * V * PF * effi if itype == "AC_3PH" else V * PF * effi
					return max(0.0, load_w / den)

				I = _current_a(load_w, voltage_v, pf, eff, install_type)
				rho_T = resistivity_ohm_m(material, ambient)
				k = _path_factor(install_type)
				# Base resistivity at 20C for reporting
				rho20 = 1.724e-8 if material == "Cu" else 2.826e-8
				lim_pct = drop_pct
				material_factor = 1.0 if material == "Cu" else 0.8
				tcf = temp_correction_factor(ambient)

				rows = []
				for awg in AWG_SIZES:
					A_m2 = AWG_AREA_MM2[awg] / 1e6
					R20_total = rho20 * (k * distance_m) / A_m2
					RT_total = rho_T * (k * distance_m) / A_m2
					V_drop = I * RT_total
					Pct = (V_drop / voltage_v) * 100.0
					base_amp = BASE_AMPACITY_CU_THHN_30C.get(awg, 0) * tcf * material_factor
					passes = (Pct <= lim_pct) and (base_amp >= 1.25 * I)
					rows.append({
						"Size": f"{awg} AWG",
						"R20_total_ohm": R20_total,
						"RT_total_ohm": RT_total,
						"V_drop_V": V_drop,
						"Pct_drop": Pct,
						"Ampacity_A": base_amp,
						"Pass": passes,
					})

				df = pd.DataFrame(rows)
				show_all = st.checkbox("Show all sizes", value=False)
				if not show_all:
					df_show = df[df["Pass"]].copy()
					if df_show.empty:
						st.warning("No AWG size passes both voltage drop and ampacity constraints. Consider increasing voltage or drop limit.")
						df_show = df.copy()
				else:
					df_show = df

				st.dataframe(
					df_show.round({"R20_total_ohm": 4, "RT_total_ohm": 4, "V_drop_V": 2, "Pct_drop": 2, "Ampacity_A": 0}),
					use_container_width=True,
				)

				# Plot percent drop vs size
				plot_df = df[["Size", "Pct_drop"]].copy()
				plot_df["Limit_%"] = lim_pct
				plot_df = plot_df.set_index("Size")
				st.line_chart(plot_df, use_container_width=True)

				if result.grounding_awg:
					st.info(f"Suggested Cu grounding conductor: AWG {result.grounding_awg} (verify per local code)")
				with st.expander("Engineering notes"):
					st.markdown(
						"- Uses DC resistance and temperature correction: R(T) = R(20°C) × [1 + α × (T − 20°C)] with α≈0.00393/°C (Cu) and 0.00403/°C (Al).\n"
						"- Voltage drop = I × R(T) with total path length = 2×distance (DC/1φ) or √3×distance (3φ).\n"
						"- Ampacity check: conservative Cu THHN base at 30°C, derated for ambient and material (Al ≈ 0.8× of Cu).\n"
						"- This ignores reactance/skin effects; suitable when voltage drop dominates and for typical frequencies.\n"
						"- Always verify with local electrical codes, installation conditions, and manufacturer data before final selection."
					)

				st.markdown("### Sanity checks")
				cA, cB, cC = st.columns(3)
				cA.metric("Ampacity", f"{result.ampacity_a:.0f} A")
				cB.metric("Ampacity margin", f"{result.ampacity_margin_pct:.0f}%")
				cC.metric("Allowable drop", f"{drop_pct:.2f}%")
				if result.grounding_awg:
					st.info(f"Suggested Cu grounding conductor: AWG {result.grounding_awg} (verify per local code)")
				st.caption("These results are conservative and should be verified against local codes and manufacturer data.")
			except Exception as e:
				st.error(f"Failed to compute sizing: {e}")

with tab3:
	st.subheader("Parts List")
	st.info("This section will generate a suggested BOM based on consumption and system assumptions. Implementation coming next.")
	with st.form("parts_form"):
		c1, c2, c3 = st.columns(3)
		sys_v = c1.selectbox("System Voltage (V)", [12, 24, 48], index=1)
		autonomy_days = c2.number_input("Autonomy (days)", min_value=0.5, value=1.0)
		dod = c3.number_input("Depth of Discharge", min_value=0.1, max_value=1.0, value=0.5)
		c4, c5, c6 = st.columns(3)
		sun_hours = c4.number_input("Peak Sun Hours", min_value=1.0, value=4.0)
		inv_eff = c5.number_input("Inverter Efficiency", min_value=0.5, max_value=1.0, value=0.92)
		bat_eff = c6.number_input("Battery Round-trip Eff.", min_value=0.5, max_value=1.0, value=0.9)
		st.form_submit_button("Generate (coming soon)")
