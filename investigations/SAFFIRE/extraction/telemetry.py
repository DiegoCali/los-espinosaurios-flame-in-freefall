"""Extract comparable test-level measurements with per-value provenance."""
from __future__ import annotations
import math
import numpy as np
from extraction.common import RAW, PROCESSED, MATRIX, TELEMETRY, read_csv, source_path, write_csv
from extraction.xlsx_reader import Workbook

PSI_TO_KPA = 6.894757293168
TARGET = "co2_increase_180s_ppm"
CHANNELS = {
    "F": ("co2_ppm", "ppm", 10000.0),
    "G": ("o2_pct", "%", 1.0),
    "H": ("flow_front_cm_s", "cm/s", 1.0),
    "I": ("flow_back_cm_s", "cm/s", 1.0),
    "J": ("pressure_kpa", "kPa", PSI_TO_KPA),
    "K": ("radiometer_1_kw_m2", "kW/m2", 0.01),
    "L": ("radiometer_2_kw_m2", "kW/m2", 0.01),
    "M": ("radiometer_3_kw_m2", "kW/m2", 0.01),
    "N": ("radiometer_4_kw_m2", "kW/m2", 0.01),
    "P": ("inlet_temperature_c", "degC", 1.0),
    **{c: (f"plume_tc_{i}_c", "degC", 1.0) for i,c in enumerate("QRSTUV",1)},
    **{c: (f"sample_tc_{i}_c", "degC", 1.0) for i,c in enumerate(["W","X","Y","Z","AA","AB"],1)},
}


def median_bins(time, arrays):
    """Use one-second medians so sample cadence does not overweight any period."""
    index = np.floor(time).astype(int)
    order = np.argsort(index, kind="stable")
    unique, start, count = np.unique(index[order], return_index=True, return_counts=True)
    output = {k: np.array([np.median(v[order[s:s+n]]) for s,n in zip(start,count)]) for k,v in arrays.items()}
    return unique.astype(float)+0.5, output, count


def robust_scale(x):
    return float(1.4826 * np.median(np.abs(x-np.median(x))))


def response_at_horizon(t, co2, horizon=180.0, window=30.0):
    before = co2[(t>=-window)&(t<0)]
    after = co2[(t>=horizon-window)&(t<horizon)]
    if len(before)<20 or len(after)<20:
        raise ValueError("Insufficient coverage of fixed CO2 windows")
    return float(np.median(after)-np.median(before)), math.hypot(robust_scale(before),robust_scale(after))


def load_sensor(i):
    path = RAW / "part-01" / f"Saffire Sensor Data Sample {i}.xlsx"
    columns = ["A","B","E","AG","AH","AR","BL"]+list(CHANNELS)
    with Workbook(path) as book:
        rows = book.rows("Calibrated Data", columns)
        _, headers = next(rows)
        _, units = next(rows)
        if headers.get("F") != "CO2" or units.get("J") != "PSIA" or units.get("F") != "%":
            raise ValueError(f"Unexpected units or schema in {path}")
        data = [r for n,r in rows if isinstance(r.get("B"),(int,float)) and r["B"]>1e12]
    arrays = {c:np.array([r.get(c,np.nan) if isinstance(r.get(c,np.nan),(int,float)) else np.nan for r in data]) for c in columns}
    if not np.all(np.diff(arrays["B"])>0):
        raise ValueError(f"Non-monotonic timestamp in {path}")
    power = arrays["AG"]*arrays["AH"]
    on = (power>20)&(arrays["AR"]>0.5)
    if not np.any(on):
        raise ValueError(f"No ignition pulse in {path}")
    t0 = float(arrays["B"][on][0])
    time = (arrays["B"]-t0)/1000
    values = {name:arrays[col]*factor for col,(name,_,factor) in CHANNELS.items()}
    values["igniter_power_w"] = power
    t, values, count = median_bins(time, values)
    if not np.all(np.isfinite(values["co2_ppm"])):
        raise ValueError(f"Missing CO2 in {path}")
    return path, arrays, time, on, t0, t, values, count


def run():
    metrics, series, dataset, conditions, validation = [], [], [], [], []
    matrix = [r for r in read_csv(RAW/MATRIX) if r.get("Sample Number","").startswith("2-")]
    if len(matrix)!=9:
        raise ValueError("Expected nine matrix tests")
    materials = ["Silicone"]*4+["SIBAL","SIBAL","PMMA_Nomex","PMMA","PMMA"]
    thickness = [0.27,0.61,1.03,0.37,0.37,0.37,0.37,10.0,10.0]
    for i, published in enumerate(matrix,1):
        test_id = f"II-{i}"
        path, a, raw_t, on, t0, t, values, count = load_sensor(i)
        source = source_path(path)
        before = (t>=-30)&(t<0)
        early = (t>=0)&(t<180)
        print(f"Extracting {test_id}: {len(raw_t)} valid sensor records",flush=True)
        def add(name,value,unit,channels,method,why,conclusion,uncertainty=None,reason=None,src=source):
            if isinstance(value,(float,np.floating)):
                value = round(float(value),9) if np.isfinite(value) else None
            metrics.append({"test_id":test_id,"metric":name,"value":value,"unit":unit,"uncertainty":round(float(uncertainty),9) if uncertainty is not None else None,"uncertainty_type":"robust_window_variability_not_calibration_or_CI" if uncertainty is not None else "not_quantified", "source_file":src,"source_channels":channels,"method":method,"selection_reason":why,"conclusion":conclusion,"reason_if_null":reason})
        flow = (values["flow_front_cm_s"]+values["flow_back_cm_s"])/2
        flow_pre = float(np.median(flow[before]))
        pressure = float(np.median(values["pressure_kpa"][before]))
        oxygen = float(np.median(values["o2_pct"][before]))
        baseline_co2 = float(np.median(values["co2_ppm"][before]))
        response, uncertainty = response_at_horizon(t,values["co2_ppm"])
        command_duration = 30.0 if i>=8 else 9.2
        command_power = 97.0 if i>=8 else 80.0
        direction = "opposed" if i==4 else "concurrent"
        dt = float(np.median(np.diff(a["B"]))/1000)
        duration = float(raw_t[on][-1]-raw_t[on][0]+dt)
        add("material",materials[i-1],"category","Material","postflight_table; documented_family_inheritance" if i in (6,9) else "postflight_table", "Selección de materiales para prevención", "Describe la composición; no implica una clasificación universal de seguridad", src=MATRIX)
        thickness_src = MATRIX if i!=8 else "part-02/SAFFIRE-II DoD.docx"
        add("thickness_nominal_mm",thickness[i-1],"mm","Sample Thickness / Table 1", "postflight_table; 037_corrected_to_0.37" if i in (4,5,6) else "preflight_nominal_10mm_not_effective_grooved_thickness" if i==8 else "postflight_table; inherited_family" if i==9 else "postflight_table", "Comparación de geometría y materiales", "Espesor nominal; II-7 se refiere al Nomex y II-8 tiene ranuras",src=thickness_src)
        add("length_cm",29.0,"cm","Sample Length","postflight_table","Escala del ensayo", "Muestras pequeñas; no representan un fuego de cabina a escala completa",src=MATRIX)
        add("width_cm",5.0,"cm","Sample Width","postflight_table","Escala del ensayo", "Ancho constante, no se estima su efecto",src=MATRIX)
        add("flow_direction",direction,"category","Flow Direction","postflight_table","Condición de propagación", "Solo II-4 es opuesta; no permite separar dirección y material/espesor",src=MATRIX)
        add("flow_pre_cm_s",flow_pre,"cm/s","H,I","median_of_two_anemometers_1s_bins_in_preignition_30s", "Condición independiente anterior al fuego", "II-6 tiene un caudal distinto de la tabla" if i==6 else "Condición medida previa a la ignición", robust_scale(flow[before]))
        add("pressure_pre_kpa",pressure,"kPa","J","PSIA_times_6.894757293168; preignition_30s_median", "Similitud de atmósfera por hábitat", "Presión cercana a terrestre; no ensaya baja presión",robust_scale(values["pressure_kpa"][before]))
        add("o2_pre_sensor_pct",oxygen,"%","G","preignition_30s_median_1s_bins", "Contexto de oxidante sin usar O2 derivado de CO2 como predictor", "Lectura de sensor; incertidumbre absoluta de calibración desconocida",robust_scale(values["o2_pct"][before]))
        add("o2_partial_pre_kpa",pressure*oxygen/100,"kPa","G,J","product_of_preignition_medians_divided_by_100", "Contexto de presión parcial", "Derivado con los mismos límites de calibración; no mide inflamabilidad en otra atmósfera")
        add("o2_table_pct",21.5 if i==1 else 22.1,"%","Percent O2 (Note 1)","table_initial_value; CO2_derived_not_independent", "Conservar discrepancia entre lectura y valor publicado", "No se usa para entrenar por su derivación de CO2",src=MATRIX)
        add("ignition_epoch_ms",t0,"ms since Unix epoch","B,AG,AH,AR","first_current_times_voltage_gt20W_and_enable_true", "Sincronizar canales dentro de la muestra", "Es tiempo del instrumento, no confirmación óptica de ignición")
        add("ignition_duration_measured_s",duration,"s","B,AG,AH,AR","span_of_power_gt20W_plus_median_sample_interval", "Validación de eventos y comparación con programa", "Duración eléctrica; no duración de combustión",dt)
        add("ignition_duration_command_s",command_duration,"s","Ignition Time","postflight_table", "Entrada conocida antes del ensayo", "Pulso programado",src=MATRIX)
        add("ignition_power_command_w",command_power,"W","Ignition Power","postflight_table", "Entrada conocida antes del ensayo", "Potencia nominal, distinta de energía realmente entregada",src=MATRIX)
        add("ignition_energy_measured_j",float(np.trapz(np.where(on,a["AG"]*a["AH"],0),raw_t)),"J","AG,AH,B,AR","trapezoid_current_times_voltage_during_enabled_pulse", "Separar ignitor de combustión", "Energía eléctrica del ignitor, no calor del fuego")
        add("co2_pre_ppm",baseline_co2,"ppm","F","percent_times10000; preignition_30s_median_1s_bins", "Referencia local para quitar acumulación previa", "El CO2 previo contiene historia de pruebas anteriores",robust_scale(values["co2_ppm"][before]))
        add(TARGET,response,"ppm","F,B,AG,AH,AR","median_CO2_150_to180s_minus_median_CO2_minus30_to0s; 1s_medians", "Nueve respuestas comparables para modelo predictivo", "Cambio de sensor a 180 s; valores negativos pequeños pueden reflejar deriva/mezcla",uncertainty)
        add("co2_peak_180s_ppm",float(np.max(values["co2_ppm"][early])),"ppm","F","max_1s_median_CO2_0_to180s", "Contexto de detección sin imponer límites de exposición", "Máximo local del sensor, no máximo espacial de la cabina")
        add("co2_end_change_ppm",float(np.median(values["co2_ppm"][-30:])-baseline_co2),"ppm","F","median_last30_1s_bins_minus_preignition_baseline", "Productos durante el registro completo", "Ventanas finales de distinta duración; no es el objetivo comparable")
        add("o2_change_180s_percentage_points",float(np.median(values["o2_pct"][(t>=150)&(t<180)])-oxygen),"percentage_points","G","median_150_to180s_minus_preignition_median", "Control de calidad de oxidante", "No equivale a consumo de O2 en entrada/salida")
        add("pressure_change_180s_kpa",float(np.median(values["pressure_kpa"][(t>=150)&(t<180)])-pressure),"kPa","J","median_150_to180s_minus_preignition_median", "Respuesta de presión en el equipo", "Señal temporal local; atribución al fuego no aislada")
        inlet = values["inlet_temperature_c"]
        add("inlet_temperature_change_180s_c",float(np.median(inlet[(t>=150)&(t<180)])-np.median(inlet[before])),"degC","P","median_150_to180s_minus_preignition_median", "Calentamiento del flujo", "Temperatura de entrada al ducto, no media de cabina")
        plume = np.array([values[f"plume_tc_{j}_c"] for j in range(1,7)])
        add("plume_peak_180s_c",float(np.max(plume[:,early])),"degC","Q:V","maximum_of_six_TC_1s_medians_0_to180s", "Cargas térmicas locales", "Cobertura geométrica limitada; no temperatura máxima de llama")
        radiation = np.array([values[f"radiometer_{j}_kw_m2"] for j in range(1,5)])
        excess = radiation - np.median(radiation[:,before],axis=1)[:,None]
        add("radiation_peak_excess_180s_kw_m2",float(np.max(excess[:,early])),"kW/m2","K:N","0.01_times_mW_per_cm2; per_channel_preignition_offset_subtracted; max_1s_median_0_to180s", "Respuesta relativa de sensores de radiación", "Flujo local dependiente de vista; incluye posible contribución del ignitor y no se transforma a HRR")
        spread = {5:2.1,6:2.6}.get(i)
        burn_time = {5:145.0,6:115.0,7:140.0,8:600.0,9:900.0}.get(i)
        outcome = "no_sustained_spread" if i<=4 else "complete_fabric_spread" if i in (5,6) else "PMMA_consumed_Nomex_not_ignited" if i==7 else "anchored_flame_slow_regression"
        add("material_outcome",outcome,"category","microgravity burn/spread columns and notes","postflight_table_and_notes", "Selección de materiales", "Resultado válido para esta condición, no garantía de autoextinción en otro hábitat",src=MATRIX)
        add("spread_rate_reported_mm_s",spread,"mm/s","microgravity Spread Rate","published_rate_transcription_not_image_measurement", "Velocidad de crecimiento cuantificada donde está disponible", "Solo dos medidas comparables de SIBAL", reason=None if spread is not None else "No numeric propagation rate; non-spread is not a measured zero speed",src=MATRIX)
        add("burn_duration_reported_s",burn_time,"s","Burn Time","published_duration_transcription", "Persistencia del fuego", "No es una entrada permitida del modelo",reason=None if burn_time is not None else "Published as insignificant, not a measured zero duration",src=MATRIX)
        add("microgravity_burn_length_reported_cm",0.0 if i<=4 else 29.0 if i in (5,6) else 5.0 if i==7 else 10.0,"cm","microgravity Burn Length and notes","published_approximate_or_component_length", "Comparación con 1g", "En PMMA 8/9 es daño visible aproximado; en II-7 solo PMMA. No son definiciones intercambiables",src=MATRIX)
        add("ground_burn_length_label",published["1-g Burn Length"],"reported_text","1-g Burn Length","verbatim_table_label", "Comparar protocolo terrestre", "Comparación contextual; no son réplicas de igual ventilación",src=MATRIX)
        for name,unit,reason in [
            ("hrr_peak_kw","kW","No paired inlet/outlet O2 and mass flow, or validated mixed cabin volume"),
            ("co_hazard_index","ratio","No CO channel or exposure limit"),
            ("co2_hazard_index","ratio","No applicable mission exposure-duration threshold supplied"),
            ("smoke_alarm_delay_s","s","No alarm threshold/event; Cygnus-Saffire clock alignment unresolved"),
            ("flow_cut_extinction_delay_s","s","No documented commanded flow-cut extinction intervention"),
            ("effective_grooved_thickness_mm","mm","No single effective thickness for grooved PMMA" if i==8 else "Not a grooved PMMA specimen"),
        ]:
            add(name,None,unit,"unavailable","not_computable", "Mantener explícitos los límites de la evidencia", "No inferible de este conjunto",reason=reason)
        for j,tj in enumerate(t):
            row={"test_id":test_id,"time_since_ignition_s":float(tj),"n_raw_records":int(count[j])}
            row.update({k:round(float(v[j]),9) for k,v in values.items()})
            row.update(source_file=source,method="per_channel_1s_median; units_converted; ignition_electrical_t0")
            series.append(row)
        conditions.append({"test_id":test_id,"mission":"Saffire-II","material":materials[i-1],"thickness_nominal_mm":thickness[i-1],"length_cm":29.0,"width_cm":5.0,"flow_pre_cm_s":round(flow_pre,9),"direction":direction,"pressure_pre_kpa":round(pressure,9),"o2_pre_sensor_pct":round(oxygen,9),"source_file":source+";"+MATRIX,"method":"see metrics.csv for each field provenance"})
        dataset.append({"test_id":test_id,"material":materials[i-1],"thickness_nominal_mm":thickness[i-1],"flow_pre_cm_s":round(flow_pre,9),"direction":direction,"ignition_duration_command_s":command_duration,"ignition_power_command_w":command_power,"structured_pmma":int(i==8),TARGET:round(response,9),"target_variability_ppm":round(uncertainty,9),"source_file":source+";"+MATRIX+(";"+thickness_src if i==8 else ""),"method":"see metrics.csv; fixed_180s_CO2_response; no_outcome_features"})
        validation.append({"test_id":test_id,"quantity":"ignition_duration_s","calculated":round(duration,6),"published":command_duration,"absolute_difference":round(abs(duration-command_duration),6),"tolerance":0.15,"status":"pass" if abs(duration-command_duration)<=0.15 else "review","source_file":source+";"+MATRIX,"method":"electrical_pulse_duration_vs_published_command"})
    write_csv(PROCESSED/"metrics.csv",metrics)
    write_csv(PROCESSED/"sensor_timeseries.csv",series)
    write_csv(PROCESSED/"tests.csv",conditions)
    write_csv(PROCESSED/"model_dataset.csv",dataset)
    write_csv(PROCESSED/"validation_checks.csv",validation)
    return metrics


def extract_cabin():
    columns = ["A","D","E","F","G","I","J","K","L"]
    with Workbook(RAW/TELEMETRY) as book:
        data=[r for n,r in book.rows("CygnusData",columns) if n>1 and isinstance(r.get("A"),(float,int))]
    records=[]
    valid_channels={"D":("cabin_temperature_c","degC",1.0,lambda v:0<v<60),"F":("cabin_pressure_kpa","kPa",PSI_TO_KPA,lambda v:5<v<20),"J":("smoke_FIZ2_obscuration_v","V",1.0,lambda v:0.01<v<5),"L":("smoke_FIZ2_scatter_v","V",1.0,lambda v:0.01<v<5)}
    for col,(name,unit,factor,valid) in valid_channels.items():
        values=np.array([r[col]*factor for r in data if isinstance(r.get(col),(int,float)) and valid(r[col])])
        for stat,fn in [("min",np.min),("median",np.median),("max",np.max),("n_nonzero_records",len)]:
            records.append({"metric":name+"_"+stat,"value":round(float(fn(values)),9) if len(values) else None,"unit":"records" if stat=="n_nonzero_records" else unit,"source_file":TELEMETRY,"source_channels":"CygnusData!"+col,"method":"physical_range_filter; remove_zero_fill; mission_record_statistic_no_test_alignment","selection_reason":"Reconocer datos de cabina y humo que sí existen","conclusion":"Registro de misión sin atribución causal a cada fuego; señales de humo sin umbral de alarma","reason_if_null":None if len(values) else "No nonzero plausible data"})
    write_csv(PROCESSED/"cabin_metrics.csv",records)
    return records
