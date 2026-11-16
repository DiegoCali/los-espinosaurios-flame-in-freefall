import type { Locale } from '@/shared/i18n';

// "How it was measured" explainers for each record. Statements come from each page's copy and
// from the exported evidence (definitions, thresholds, partitions). No new results.
const en = {
  saffire: {
    index: 'HOW IT WAS MEASURED / CO₂ RESPONSE', title: 'FROM A SENSOR TRACE TO ONE NUMBER.',
    intro: 'Each SAFFIRE-II test leaves a CO₂ trace. The response is the median of 1-s CO₂ medians at [150, 180) s minus the median at [−30, 0) s, with electrical ignition as t = 0. Pick a test: the number is recomputed live from its real series.',
    steps: [['01 / IGNITION REFERENCE', 'Electrical ignition defines t = 0.'], ['02 / BASELINE WINDOW', 'Median CO₂ between −30 s and 0 s.'], ['03 / RESPONSE WINDOW', 'Median CO₂ between 150 s and 180 s.'], ['04 / DIFFERENCE', 'Response minus baseline: a signed local change in ppm.']],
    baseline: 'BASELINE [−30, 0) s', window: 'WINDOW [150, 180) s', delta: 'Δ CO₂ AT 180 s', exported: 'EXPORTED VALUE', recomputed: 'RECOMPUTED HERE',
    material: 'MATERIAL', flow: 'AIR VELOCITY', time: 'TIME FROM IGNITION (s)', ppm: 'ABSOLUTE CO₂ (ppm)',
    warning: 'A local sensor change; it does not represent total hazard. Small negative values may reflect drift or mixing.',
    loading: 'LOADING SENSOR SERIES', error: 'The sensor series could not be loaded.',
    micro: 'In microgravity, combustion products are not carried upward by a buoyant plume; the forced air flow sets how they reach the sensor.',
  },
  same: {
    index: 'HOW IT WAS MEASURED / SMOKE DETECTION', title: 'ONE SMOKE PUSH. TWO DETECTION PRINCIPLES.',
    intro: 'A smoke push reaches two detectors. The photoelectric detector registers light scattered by particles; the ionization detector registers a change in ion current. The project labels a response with proxy thresholds.',
    regimes: ['WITH FLOW ~8 cm/s', 'NO FLOW'], regime: 'FLOW REGIME',
    detectors: ['ISS PHOTOELECTRIC', 'IONIZATION'], rules: ['Scatter drop ≥ 1 V', 'Rise ≥ 0.5 V'],
    rate: 'FRACTION OF PUSHES WITH A RESPONSE', pushes: 'labelled pushes',
    why: 'Without flow (possible only in microgravity, where there is no buoyant plume) smoke lingers at the source and coagulates: larger particles, fewer of them. Different particle sizes affect the detection principles differently.',
    proxy: 'Proxy thresholds, not official flight alarms. Particle motion drawn here is conceptual; the percentages are real.',
    beam: 'LIGHT SOURCE', sensor: 'PHOTODIODE', chamber: 'ION CHAMBER', signal: 'DIAGRAM · CONCEPTUAL', source: 'SMOKE SOURCE',
  },
  acme: {
    index: 'HOW IT WAS CALCULATED / Tad', title: 'NORMAL OR INVERSE: WHO FEEDS THE FLAME?',
    intro: 'In a normal flame, fuel leaves the burner into oxygen. In an inverse flame, oxygen leaves the burner into ethylene. A frozen Ridge regression maps seven initial conditions to a calculated adiabatic temperature.',
    configs: ['NORMAL', 'INVERSE'], burner: 'BURNER', ambient: 'AMBIENT', fuel: 'FUEL', oxygen: 'OXYGEN', ethylene: 'ETHYLENE (C₂H₄)',
    inputs: ['Flame type', 'Burner reactant fraction', 'Ambient reactant fraction', 'Reactant flow (mg/s)', 'Nitrogen flow (mg/s)', 'Total flow (mg/s)', 'Initial pressure (atm)'],
    model: 'FROZEN RIDGE MODEL', output: 'CALCULATED Tad / K',
    partitions: ['TRAINING', 'VALIDATION', 'HOLDOUT'], holdout: 'HOLDOUT RMSE BY FLAME TYPE / K',
    notMeasured: 'Tad is a calculated adiabatic temperature: it is not the flame temperature, nor a measure of soot or extinction.',
    micro: 'Without buoyancy the diffusion flame is not stretched upward; the reactant roles at the burner and in the surroundings set its structure.',
    diagram: 'CONCEPTUAL DIAGRAM · NOT REAL SIZE OR TEMPERATURE',
  },
  ambient: { label: 'MICROGRAVITY · g ≈ 0' },
};
type MeasureCopy = typeof en;
const es: MeasureCopy = {
  saffire: {
    index: 'CÓMO SE MIDIÓ / RESPUESTA DE CO₂', title: 'DE UNA SEÑAL DE SENSOR A UN NÚMERO.',
    intro: 'Cada ensayo SAFFIRE-II deja una señal de CO₂. La respuesta es la mediana de medianas de 1 s en [150, 180) s menos la mediana en [−30, 0) s, con la ignición eléctrica como t = 0. Elige un ensayo: el número se recalcula en vivo a partir de su serie real.',
    steps: [['01 / REFERENCIA DE IGNICIÓN', 'La ignición eléctrica define t = 0.'], ['02 / VENTANA BASE', 'Mediana de CO₂ entre −30 s y 0 s.'], ['03 / VENTANA DE RESPUESTA', 'Mediana de CO₂ entre 150 s y 180 s.'], ['04 / DIFERENCIA', 'Respuesta menos base: un cambio local con signo, en ppm.']],
    baseline: 'BASE [−30, 0) s', window: 'VENTANA [150, 180) s', delta: 'Δ CO₂ A 180 s', exported: 'VALOR EXPORTADO', recomputed: 'RECALCULADO AQUÍ',
    material: 'MATERIAL', flow: 'VELOCIDAD DEL AIRE', time: 'TIEMPO DESDE LA IGNICIÓN (s)', ppm: 'CO₂ ABSOLUTO (ppm)',
    warning: 'Cambio local del sensor; no equivale a peligro total. Valores negativos pequeños pueden reflejar deriva o mezcla.',
    loading: 'CARGANDO SERIE DEL SENSOR', error: 'No se pudo cargar la serie del sensor.',
    micro: 'En microgravedad, los productos de combustión no ascienden con un penacho flotante; el flujo de aire forzado determina cómo llegan al sensor.',
  },
  same: {
    index: 'CÓMO SE MIDIÓ / DETECCIÓN DE HUMO', title: 'UN PULSO DE HUMO. DOS PRINCIPIOS DE DETECCIÓN.',
    intro: 'Un pulso de humo llega a dos detectores. El fotoeléctrico registra la luz dispersada por las partículas; el de ionización registra un cambio en la corriente de iones. El proyecto etiqueta una respuesta con umbrales proxy.',
    regimes: ['CON FLUJO ~8 cm/s', 'SIN FLUJO'], regime: 'RÉGIMEN DE FLUJO',
    detectors: ['FOTOELÉCTRICO ISS', 'IONIZACIÓN'], rules: ['Caída de dispersión ≥ 1 V', 'Aumento ≥ 0.5 V'],
    rate: 'FRACCIÓN DE PULSOS CON RESPUESTA', pushes: 'pulsos etiquetados',
    why: 'Sin flujo (solo posible en microgravedad, donde no hay penacho flotante) el humo permanece en la fuente y coagula: partículas más grandes y menos numerosas. Los distintos tamaños afectan de forma diferente a cada principio de detección.',
    proxy: 'Umbrales proxy, no alarmas oficiales de vuelo. El movimiento de partículas es conceptual; los porcentajes son reales.',
    beam: 'FUENTE DE LUZ', sensor: 'FOTODIODO', chamber: 'CÁMARA DE IONES', signal: 'ESQUEMA · CONCEPTUAL', source: 'FUENTE DE HUMO',
  },
  acme: {
    index: 'CÓMO SE CALCULÓ / Tad', title: 'NORMAL O INVERSA: ¿QUIÉN ALIMENTA LA LLAMA?',
    intro: 'En una llama normal, el combustible sale del quemador hacia el oxígeno. En una inversa, el oxígeno sale del quemador hacia el etileno. Una regresión Ridge congelada relaciona siete condiciones iniciales con una temperatura adiabática calculada.',
    configs: ['NORMAL', 'INVERSA'], burner: 'QUEMADOR', ambient: 'AMBIENTE', fuel: 'COMBUSTIBLE', oxygen: 'OXÍGENO', ethylene: 'ETILENO (C₂H₄)',
    inputs: ['Tipo de llama', 'Fracción en quemador', 'Fracción ambiental', 'Flujo del reactivo (mg/s)', 'Flujo de nitrógeno (mg/s)', 'Flujo total (mg/s)', 'Presión inicial (atm)'],
    model: 'MODELO RIDGE CONGELADO', output: 'Tad CALCULADA / K',
    partitions: ['ENTRENAMIENTO', 'VALIDACIÓN', 'RESERVA'], holdout: 'RMSE RESERVADO POR TIPO DE LLAMA / K',
    notMeasured: 'Tad es una temperatura adiabática calculada: no es la temperatura de la llama, ni una medida de hollín o extinción.',
    micro: 'Sin flotabilidad la llama de difusión no se estira hacia arriba; los papeles de los reactivos en el quemador y en el ambiente definen su estructura.',
    diagram: 'ESQUEMA CONCEPTUAL · NO REPRESENTA TAMAÑO NI TEMPERATURA REAL',
  },
  ambient: { label: 'MICROGRAVEDAD · g ≈ 0' },
};
export const measureCopy: Record<Locale, MeasureCopy> = { en, es };
export type { MeasureCopy };
