import type { Locale } from '@/shared/i18n';

// "Fire aboard a spacecraft" cinematic. Sources: investigations/SAFFIRE/SAFFIRE_EXPLICADO.md,
// SAFFIRE_ANALYSIS_REPORT_EN.md and the exported SAFFIRE evidence. The launch prologue is illustrative.
const en = {
  index: 'MISSION SAFFIRE-II · PSI-99', title: 'A FIRE ABOARD A SPACECRAFT.',
  intro: 'Scroll to follow a real SAFFIRE-II test: from orbit, into the flow duct, through ignition, to the single number the team computes from the CO₂ sensor.',
  pick: 'CHOOSE A REAL TEST', scroll: 'SCROLL TO ADVANCE THE MISSION ↓',
  stages: [
    { tag: 'PROLOGUE · ILLUSTRATIVE', title: 'LAUNCH', body: 'Every spacecraft reaches orbit on a launch vehicle. This prologue is illustrative and is not part of the data.' },
    { tag: 'ORBIT', title: 'AN UNCREWED CARGO SPACECRAFT', body: 'NASA ignited material specimens inside an uncrewed Cygnus spacecraft in microgravity. The nine tests share one vehicle and one cabin history.' },
    { tag: 'INSIDE THE VEHICLE', title: 'THE FLOW DUCT', body: 'A specimen of 29 × 5 cm sits in a duct with forced air flow. Thermocouples, radiometers and gas sensors record the event.' },
    { tag: 'WINDOW [−30, 0) s', title: 'BASELINE BEFORE IGNITION', body: 'The median CO₂ reading in the 30 s before ignition defines this test’s local baseline. It retains CO₂ accumulated from earlier tests.' },
    { tag: 't = 0', title: 'IGNITION', body: 'The igniter receives its commanded power and duration. The electrical marker defines t = 0; it is not a verified optical ignition time.' },
    { tag: '0 → 180 s', title: 'THE FLAME AND ITS PRODUCTS', body: 'Combustion products travel with the duct flow toward the local CO₂ sensor. The flame behaviour shown follows the documented outcome of this test.' },
    { tag: 'WINDOW [150, 180) s', title: 'HOW IT IS CALCULATED', body: 'Response minus baseline gives one comparable, signed number per test. A two-group model then relates it to material and flow.' },
  ],
  outcomes: {
    no_sustained_spread: 'No sustained spread', complete_fabric_spread: 'Complete fabric spread',
    PMMA_consumed_Nomex_not_ignited: 'PMMA lead-in consumed; Nomex not ignited', anchored_flame_slow_regression: 'Anchored flame; slow regression',
  } as Record<string, string>,
  materials: { Silicone: 'Silicone', SIBAL: 'SIBAL (cotton / fiberglass)', PMMA_Nomex: 'PMMA–Nomex composite', PMMA: 'PMMA' } as Record<string, string>,
  directions: { concurrent: 'concurrent', opposed: 'opposed' } as Record<string, string>,
  labels: {
    material: 'MATERIAL', thickness: 'THICKNESS', flow: 'PRE-IGNITION FLOW', direction: 'DIRECTION', o2: 'O₂ SENSOR', pressure: 'PRESSURE',
    igniter: 'IGNITER COMMAND', marker: 'IGNITION MARKER (UTC)', outcome: 'DOCUMENTED OUTCOME', rate: 'PUBLISHED SPREAD RATE', plume: 'PLUME PEAK · FIRST 180 s',
    time: 'T FROM IGNITION', co2: 'CO₂ READING', delta: 'READING − BASELINE', front: 'FLAME FRONT (FROM PUBLISHED RATE)', none: 'not published',
  },
  scene: {
    duct: 'FLOW DUCT', flowWord: 'AIR FLOW', sample: 'SPECIMEN 29 × 5 cm', igniter: 'IGNITER', tc: 'THERMOCOUPLES', radiometer: 'RADIOMETER',
    co2: 'CO₂', o2: 'O₂', cutaway: 'CUTAWAY · CONCEPTUAL · POSITIONS SCHEMATIC', orbit: 'CONCEPTUAL · NOT TO SCALE', leadIn: 'PMMA LEAD-IN', nomex: 'NOMEX',
  },
  calc: {
    title: 'THE CALCULATION', response: 'median CO₂ [150, 180) s', baseline: 'median CO₂ [−30, 0) s', delta: 'Δ CO₂ at 180 s',
    model: 'SELECTED MODEL · REFIT ON ALL 9 TESTS', silicone: 'silicone', other: 'other materials', thisTest: 'For this test',
    heldOut: 'HELD-OUT PREDICTION (LEAVE-ONE-TEST-OUT)', residual: 'residual', rmse: 'LOOCV RMSE', baselineRmse: 'training-mean baseline',
    caveat: 'A local sensor response at one horizon: not total heat, toxic dose or hazard. Nine tests in one flight; the repeated selection makes the best RMSE optimistic.',
  },
  simulate: 'OPEN THE FULL SIMULATION', simulateNote: 'Mission control · 3D spacecraft · real data',
  craft: { cargo: 'CARGO MODULE · EXPERIMENT INSIDE', service: 'SERVICE MODULE', arrays: 'SOLAR ARRAYS' },
  motion: 'Flame motion is conceptual: only SIBAL (II-5, II-6) has published spread rates. CO₂ values are the real sensor series.',
  source: 'SOURCES: NASA PSI SAFFIRE-II (doi:10.60555/2chp-m469) · team analysis investigations/SAFFIRE',
};
type SpacecraftCopy = typeof en;
const es: SpacecraftCopy = {
  index: 'MISIÓN SAFFIRE-II · PSI-99', title: 'UN INCENDIO A BORDO DE UNA NAVE.',
  intro: 'Desplázate para seguir un ensayo real de SAFFIRE-II: desde la órbita, al interior del ducto de flujo, a la ignición y al único número que el equipo calcula a partir del sensor de CO₂.',
  pick: 'ELIGE UN ENSAYO REAL', scroll: 'DESPLÁZATE PARA AVANZAR LA MISIÓN ↓',
  stages: [
    { tag: 'PRÓLOGO · ILUSTRATIVO', title: 'LANZAMIENTO', body: 'Toda nave llega a órbita en un vehículo de lanzamiento. Este prólogo es ilustrativo y no forma parte de los datos.' },
    { tag: 'ÓRBITA', title: 'UNA NAVE DE CARGA SIN TRIPULACIÓN', body: 'La NASA encendió muestras de materiales dentro de una nave Cygnus sin tripulación, en microgravedad. Los nueve ensayos comparten un mismo vehículo y una misma historia de cabina.' },
    { tag: 'DENTRO DEL VEHÍCULO', title: 'EL DUCTO DE FLUJO', body: 'Una muestra de 29 × 5 cm se ubica en un ducto con flujo de aire forzado. Termopares, radiómetros y sensores de gases registran el evento.' },
    { tag: 'VENTANA [−30, 0) s', title: 'LÍNEA BASE ANTES DE LA IGNICIÓN', body: 'La mediana de CO₂ en los 30 s previos a la ignición define la línea base local del ensayo. Conserva el CO₂ acumulado de ensayos anteriores.' },
    { tag: 't = 0', title: 'IGNICIÓN', body: 'El ignitor recibe su potencia y duración programadas. El marcador eléctrico define t = 0; no es un tiempo de ignición óptica verificado.' },
    { tag: '0 → 180 s', title: 'LA LLAMA Y SUS PRODUCTOS', body: 'Los productos de combustión viajan con el flujo del ducto hacia el sensor local de CO₂. El comportamiento de la llama sigue el resultado documentado de este ensayo.' },
    { tag: 'VENTANA [150, 180) s', title: 'CÓMO SE CALCULA', body: 'Respuesta menos línea base da un número comparable y con signo por ensayo. Luego un modelo de dos grupos lo relaciona con el material y el flujo.' },
  ],
  outcomes: {
    no_sustained_spread: 'Sin propagación sostenida', complete_fabric_spread: 'Propagación completa en el tejido',
    PMMA_consumed_Nomex_not_ignited: 'Tramo inicial de PMMA consumido; Nomex no encendió', anchored_flame_slow_regression: 'Llama anclada; regresión lenta',
  },
  materials: { Silicone: 'Silicona', SIBAL: 'SIBAL (algodón / fibra de vidrio)', PMMA_Nomex: 'Compuesto PMMA–Nomex', PMMA: 'PMMA' },
  directions: { concurrent: 'concurrente', opposed: 'opuesto' },
  labels: {
    material: 'MATERIAL', thickness: 'ESPESOR', flow: 'FLUJO PREVIO', direction: 'DIRECCIÓN', o2: 'SENSOR O₂', pressure: 'PRESIÓN',
    igniter: 'IGNITOR PROGRAMADO', marker: 'MARCADOR DE IGNICIÓN (UTC)', outcome: 'RESULTADO DOCUMENTADO', rate: 'TASA PUBLICADA', plume: 'PICO DE PENACHO · PRIMEROS 180 s',
    time: 'T DESDE LA IGNICIÓN', co2: 'LECTURA CO₂', delta: 'LECTURA − BASE', front: 'FRENTE (SEGÚN TASA PUBLICADA)', none: 'no publicada',
  },
  scene: {
    duct: 'DUCTO DE FLUJO', flowWord: 'FLUJO DE AIRE', sample: 'MUESTRA 29 × 5 cm', igniter: 'IGNITOR', tc: 'TERMOPARES', radiometer: 'RADIÓMETRO',
    co2: 'CO₂', o2: 'O₂', cutaway: 'CORTE · CONCEPTUAL · POSICIONES ESQUEMÁTICAS', orbit: 'CONCEPTUAL · SIN ESCALA', leadIn: 'TRAMO PMMA', nomex: 'NOMEX',
  },
  calc: {
    title: 'EL CÁLCULO', response: 'mediana CO₂ [150, 180) s', baseline: 'mediana CO₂ [−30, 0) s', delta: 'Δ CO₂ a 180 s',
    model: 'MODELO SELECCIONADO · REAJUSTADO CON LOS 9 ENSAYOS', silicone: 'silicona', other: 'otros materiales', thisTest: 'Para este ensayo',
    heldOut: 'PREDICCIÓN RESERVADA (DEJANDO UN ENSAYO FUERA)', residual: 'residuo', rmse: 'RMSE LOOCV', baselineRmse: 'línea base de media',
    caveat: 'Respuesta local de un sensor en un horizonte: no es calor total, dosis tóxica ni peligro. Nueve ensayos en un vuelo; la selección repetida hace optimista el mejor RMSE.',
  },
  simulate: 'VER SIMULACIÓN COMPLETA', simulateNote: 'Control de misión · nave 3D · datos reales',
  craft: { cargo: 'MÓDULO DE CARGA · EXPERIMENTO DENTRO', service: 'MÓDULO DE SERVICIO', arrays: 'PANELES SOLARES' },
  motion: 'El movimiento de la llama es conceptual: solo SIBAL (II-5, II-6) tiene tasas de propagación publicadas. Los valores de CO₂ son la serie real del sensor.',
  source: 'FUENTES: NASA PSI SAFFIRE-II (doi:10.60555/2chp-m469) · análisis del equipo investigations/SAFFIRE',
};
export const spacecraftCopy: Record<Locale, SpacecraftCopy> = { en, es };
export type { SpacecraftCopy };
