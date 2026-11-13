from __future__ import annotations
import numpy as np

RELEVANCE="identify_relevant_investigations"
PREDICTION="predictive_modeling_data"
CONTROLS="next_gen_fire_safety_controls"
ENVIRONMENTS={
    "iss_like_spacecraft":{"o2_pct":21.0,"pressure_kpa":101.3,"gravity_g":0.0},
    "lunar_base":{"o2_pct":34.0,"pressure_kpa":56.5,"gravity_g":0.165},
    "pressurized_rover":{"o2_pct":34.0,"pressure_kpa":56.5,"gravity_g":0.165},
    "mars_base":{"o2_pct":26.5,"pressure_kpa":70.3,"gravity_g":0.38},
    "gateway_like_station":{"o2_pct":21.0,"pressure_kpa":101.3,"gravity_g":0.0},
}


def value(test,section,key):
    return test[section][key]["value"]


def ranking(tests):
    assumptions={name:{**v,"oxygen_partial_pressure_kpa":v["o2_pct"]*v["pressure_kpa"]/100,"status":"analyst_design_assumption_not_actual_mission_specification","source_file":"DATA_PLAN.md","method":"explicit_hypothetical_environment_scenario","conclusion":"Permite ordenar similitud, no certificar seguridad ni predecir cambio de gravedad"} for name,v in ENVIRONMENTS.items()}
    ranked={}
    for name,env in ENVIRONMENTS.items():
        rows=[]
        for test in tests:
            oxygen=value(test,"conditions","o2_pre_sensor_pct")
            pressure=value(test,"conditions","pressure_pre_kpa")
            area=value(test,"conditions","length_cm")*value(test,"conditions","width_cm")/10000
            oxygen_component=30*max(0,1-abs(oxygen-env["o2_pct"])/20)
            pressure_component=25*max(0,1-abs(pressure-env["pressure_kpa"])/60)
            gravity_component=15*np.exp(-abs(env["gravity_g"])/.2)
            size_component=5*min(1,area/.04)
            outcome=value(test,"results","material_outcome")
            fire_component=5 if outcome=="complete_fabric_spread" else 4 if outcome=="anchored_flame_slow_regression" else 3
            data_component=6+4*int(value(test,"results","spread_rate_reported_mm_s") is not None)
            ground_component=10*int(bool(value(test,"results","ground_burn_length_label")))
            components={"oxygen_similarity":oxygen_component,"pressure_similarity":pressure_component,"gravity_similarity":gravity_component,"sample_scale":size_component,"fire_behavior":fire_component,"quantitative_data":data_component,"ground_comparison":ground_component}
            rows.append({"test_id":test["test_id"],"score":round(sum(components.values()),2),"components":{k:round(float(v),3) for k,v in components.items()},"conclusion":"Relevancia comparativa bajo supuestos; no nivel de riesgo del material","source_file":["data/processed/metrics.csv","DATA_PLAN.md"],"method":"fixed_weighted_rubric_v1","transfer_to_environment_validated":False})
        rows.sort(key=lambda r:(-r["score"],r["test_id"]))
        for i,row in enumerate(rows,1):row["rank"]=i
        ranked[name]=rows
    return {"rubric":"Score /100: O2 30*max(0,1-|delta percentage points|/20); P 25*max(0,1-|delta kPa|/60); gravity 15*exp(-|g_environment-0|/0.2); area 5*min(1,area/0.04m2); behavior 5 fabric spread, 4 anchored PMMA, 3 otherwise; data 6 for gas/thermal +4 for published numeric spread; ground-comparison 10 if available. Ties ordered by test_id. Differences smaller than sensor uncertainty are not scientifically significant.","environment_assumptions":assumptions,"environments":ranked,"limitations":["Weights and normalizing scales are analyst judgments, not calibrated probabilities","The same atmosphere assumptions for lunar base and rover intentionally yield equal rankings","All tests are microgravity, not lunar or Martian partial gravity","All samples have area 0.0145 m2; none demonstrates full-cabin fire scaling","No prediction at exploration atmospheres is validated"]}


def compute(tests,cabin,autoresearch,inventory):
    sibal=[t for t in tests if value(t,"conditions","material")=="SIBAL"]
    silicone=[t for t in tests if value(t,"conditions","material")=="Silicone"]
    flows=[value(t,"conditions","flow_pre_cm_s") for t in sibal]
    speeds=[value(t,"results","spread_rate_reported_mm_s") for t in sibal]
    pressure=[value(t,"conditions","pressure_pre_kpa") for t in tests]
    oxygen=[value(t,"conditions","o2_pre_sensor_pct") for t in tests]
    baselines=[value(t,"results","co2_pre_ppm") for t in tests]
    response=[value(t,"results","co2_increase_180s_ppm") for t in tests]
    findings={
        "materials":{"silicone_tests":len(silicone),"silicone_no_sustained_spread":sum(value(t,"results","material_outcome")=="no_sustained_spread" for t in silicone),"sibal_tests":len(sibal),"sibal_complete_spread":sum(value(t,"results","material_outcome")=="complete_fabric_spread" for t in sibal),"sibal_spread_rates_mm_s":speeds,"sibal_flow_cm_s":flows,"sibal_relative_speed_increase":speeds[1]/speeds[0]-1,"nomex_result":"PMMA lead-in consumed, Nomex did not ignite; single composite test","pmma_result":"Two slabs sustained anchored flames; damage length is not a spread trajectory","conclusion":"Material, geometry, gravity and ventilation all constrain interpretation; no material is declared universally fire-safe","source_file":"data/processed/metrics.csv","method":"group_by_documented_material_and_published_outcome"},
        "habitat_atmosphere":{"pressure_kpa_range":[min(pressure),max(pressure)],"sensor_o2_pct_range":[min(oxygen),max(oxygen)],"observed_gravity_g":0,"conclusion":"Near terrestrial pressure and airlike oxygen only; no local low-pressure, oxygen-enriched tests","source_file":"data/processed/metrics.csv","method":"range_of_preignition_medians","note":"Sensor O2 absolute calibration is not independently established"},
        "suppression":{"note":"No controlled cut-flow extinction intervention can be identified in this set","flow_cut_extinction_delay_s":None,"conclusion":"No inference on ventilation shutoff effectiveness","source_file":"data/processed/metrics.csv","method":"unavailable_intervention"},
        "detection_and_products":{"co2_response_180s_ppm_range":[min(response),max(response)],"co2_pre_ppm_range":[min(baselines),max(baselines)],"smoke_records_present":any("smoke_" in r["metric"] and r["value"] is not None for r in cabin),"alarm_delays_s":None,"co_hazard_index":None,"co2_hazard_index":None,"conclusion":"CO2 response can be compared; alarm timing and crew exposure risk cannot be calculated","source_file":["data/processed/metrics.csv","data/processed/cabin_metrics.csv"],"method":"fixed_window_response_ranges; explicit_missing_alarm_and_exposure_data"},
        "cabin_impact":{"mission_record_statistics":cabin,"note":"Statistics exclude zero fill; clocks not synchronized to individual tests; no causal attribution or spatial cabin average","conclusion":"There is useful cabin/smoke telemetry but it needs clock reconstruction and calibration for equipment design"},
    }
    best=autoresearch["best"]
    baseline=autoresearch["baseline"]
    best_rmse=best.get("val_rmse")
    baseline_rmse=baseline.get("val_rmse")
    statements=[
        ("K1",RELEVANCE,f"Los {inventory['n_files']} archivos contienen nueve pruebas medidas de Saffire-II, identificadas localmente como PSI-99; no aportan seis misiones independientes.",["/data_inventory_summary/n_files","/data_inventory_summary/missions_found","/data_inventory_summary/identified_psi_investigation"],"high"),
        ("K2",RELEVANCE,f"La presión previa medida abarca {min(pressure):.2f}–{max(pressure):.2f} kPa y el O2 del sensor {min(oxygen):.2f}–{max(oxygen):.2f}%; la similitud atmosférica favorece los escenarios ISS/Gateway asumidos.",["/findings/habitat_atmosphere","/relevance_ranking/environment_assumptions","/relevance_ranking/environments"],"medium"),
        ("K3",RELEVANCE,"Las bases lunares y marcianas y el rover reciben un ranking de transferencia condicionado: ninguna prueba local valida baja presión, O2 enriquecido o gravedad parcial.",["/findings/habitat_atmosphere/observed_gravity_g","/relevance_ranking/limitations"],"medium"),
        ("K4",PREDICTION,f"El piloto de nueve pruebas obtiene RMSE LOOCV {best_rmse:.2f} ppm frente a {baseline_rmse:.2f} ppm de la media de entrenamiento; la selección usa la misma CV y requiere validación externa.",["/autoresearch/n_rows","/autoresearch/baseline/val_rmse","/autoresearch/best/val_rmse","/predictive_model/cv_predictions"],"low"),
        ("K5",PREDICTION,f"Las dos pruebas SIBAL publican {speeds[0]:.1f} y {speeds[1]:.1f} mm/s con caudal medido de {flows[0]:.2f} y {flows[1]:.2f} cm/s: un aumento de velocidad de {(speeds[1]/speeds[0]-1)*100:.1f}%, descriptivo con n=2.",["/findings/materials/sibal_spread_rates_mm_s","/findings/materials/sibal_flow_cm_s","/findings/materials/sibal_relative_speed_increase"],"low"),
        ("K6",PREDICTION,f"El CO2 previo varía entre {min(baselines):.0f} y {max(baselines):.0f} ppm; restar la línea base local evita confundir acumulación de pruebas previas con la respuesta del ensayo.",["/findings/detection_and_products/co2_pre_ppm_range","/tests/0/results/co2_increase_180s_ppm/method"],"medium"),
        ("K7",CONTROLS,f"Las {len(silicone)} muestras de silicona no sostuvieron propagación en estas condiciones; sus comparaciones de 1g muestran que material y régimen de gravedad/flujo deben conservarse al interpretar la selección preventiva.",["/findings/materials/silicone_tests","/findings/materials/silicone_no_sustained_spread","/tests/0/results/ground_burn_length_label","/tests/3/results/ground_burn_length_label"],"medium"),
        ("K8",CONTROLS,"Hay señales de humo de Cygnus, pero faltan umbrales/eventos de alarma y una sincronización verificada; no se informa un tiempo de detección ni un margen seguro para la tripulación.",["/findings/detection_and_products/smoke_records_present","/findings/detection_and_products/alarm_delays_s","/findings/cabin_impact/note"],"low"),
        ("K9",CONTROLS,"Faltan O2 de entrada/salida con caudal másico y una intervención documentada de corte de flujo; los datos no dimensionan por sí solos HRR ni eficacia de supresión.",["/tests/0/results/hrr_peak_kw","/findings/suppression"],"medium"),
    ]
    insights=[{"id":k,"objective":o,"statement":s,"evidence":e,"confidence":c} for k,o,s,e,c in statements]
    return findings,ranking(tests),insights


if __name__=="__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from analysis.build_analysis_json import build
    result=build()
    print(f"Computed {len(result['key_insights'])} traced insights; analysis/output/insights.json")
