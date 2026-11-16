import type { Locale } from '@/shared/i18n';

// Copy for the animated Home explainers. Every statement is taken from project sources:
// investigations/BASS-II/knowledge/physics/flame_spread_physics.md §3–4, the per-study
// page copy and the exported evidence JSON files. Nothing here is a new result.
const en = {
  gravity: {
    index: '01 / WHY MICROGRAVITY', title: 'SAME FLAME. NO BUOYANCY.',
    intro: 'Gravity changes how a flame receives oxygen. Switch the regime to see the conceptual difference described in the BASS-II knowledge base.',
    modes: ['1 g · EARTH', 'μg · ORBIT', 'LOW FLOW · QUENCH'],
    mode: 'REGIME',
    panels: [
      { tag: 'BUOYANT PLUME', title: 'ON EARTH, HOT GASES RISE', body: 'Buoyancy creates a rising plume that stretches the flame upward. Yellow-orange light is incandescent soot.' },
      { tag: 'NO RISING PLUME', title: 'IN ORBIT, THE FLAME SPREADS OUT', body: 'Without buoyancy there is no rising plume. The flame is thicker, wider and shorter, with a larger standoff (diffusion plus forced flow). It appears oval, hemispherical or circular.' },
      { tag: 'NEAR EXTINCTION', title: 'AT LOW FLOW, IT SHRINKS AND GOES OUT', body: 'At low opposed flow the flame shortens and narrows until it becomes circular, blue, and extinguishes. In BASS-II this occurs at 1–5 cm/s.' },
    ],
    colour: 'COLOUR', colourNote: 'Blue is chemiluminescence (CH*, C₂*). Yellow-orange is incandescent soot. At low flow less soot forms and the flame appears blue.',
    oxygen: 'O₂ SUPPLY', oxygenModes: ['Drawn in by the plume', 'Diffusion + forced flow', 'Diffusion-limited'],
    shape: 'SHAPE', shapeModes: ['Tall teardrop', 'Oval / hemispherical', 'Small circle → out'],
    diagram: 'CONCEPTUAL DIAGRAM / NOT NASA FOOTAGE',
    source: 'SOURCE: BASS-II KNOWLEDGE BASE · FLAME SHAPE AND COLOUR IN μg (Link 2018; NASA TM §6.1.4)',
  },
  rail: {
    index: '02 / FIVE MISSIONS', title: 'FIVE PHENOMENA. FIVE LIVE RECORDS.', intro: 'Scroll through the archive. Each record shows one real figure from its exported evidence; diagrams are conceptual.',
    open: 'OPEN RECORD', drag: 'SCROLL TO TRAVERSE →',
    facts: {
      acme: [['MODEL CASES', '236'], ['CONFIGURATIONS', 'NORMAL / INVERSE'], ['HOLDOUT RMSE', 'K']],
      'bass-ii': [['PROCESSED TESTS', '83'], ['STEADY RATES', '54'], ['PUBLISHED COMPARISONS', '25']],
      'saffire-ii': [['TESTS ANALYZED', '9'], ['TEST II-7 · 180 S', 'ppm'], ['SENSOR', 'LOCAL CO₂']],
      'same-r': [['PHOTOELECTRIC · WITH FLOW', '%'], ['IONIZATION · WITH FLOW', '%'], ['TESTS WITH TELEMETRY', '47']],
      flex: [['DOCUMENTED TESTS', '274'], ['ENDED BY EXTINCTION', '186'], ['FUELS', 'METHANOL / HEPTANE']],
    } as Record<string, [string, string][]>,
    notes: {
      acme: 'Burner: fuel / ambient: oxygen — and the inverse. Diagram, not a measured flame.',
      'bass-ii': 'A flame front crossing a sample. Edge positions come from calibrated video.',
      'saffire-ii': 'Real absolute CO₂ reading for test II-7. Local response; not total hazard.',
      'same-r': 'Fresh smoke ages and clusters. Project proxy thresholds, not alarms.',
      flex: 'A droplet shrinks as it burns. Conceptual diagram, not to scale.',
    } as Record<string, string>,
  },
  front: {
    index: '03 / FROM VIDEO TO VELOCITY', title: 'WATCH A REAL FLAME FRONT ADVANCE.',
    intro: 'Test B1 · PMMA thin film. Scroll to replay the leading-edge positions extracted from calibrated NASA video, frame by frame.',
    steps: [
      ['01 / OBSERVE', 'The visible edge of the flame changes position between frames.'],
      ['02 / MEASURE', 'Each point is a position calculated from a calibrated frame. They are measurements, not forecasts.'],
      ['03 / FIT', 'The slope over a stable interval approximates the spread velocity V_f.'],
      ['04 / COMPARE', 'In B1, the calculated rate closely matches the published value. This agreement belongs to the development set.'],
    ],
    time: 'VIDEO TIME', edge: 'LEADING EDGE', measured: 'MEASURED IN VIDEO', published: 'PUBLISHED', interval: 'STEADY INTERVAL',
    thickness: 'THICKNESS', flow: 'INITIAL FLOW', oxygen: 'INITIAL O₂', strip: 'FLAME FRONT POSITION ON THE SAMPLE (SCHEMATIC STRIP)',
    loading: 'LOADING B1 SERIES', error: 'The B1 series could not be loaded.',
    warning: 'Optical extraction may include noise. It is not equivalent to a physical ruler inside the experiment.',
    introMulti: 'Choose one of the three tests whose series are exported. Scroll to replay the leading-edge positions extracted from calibrated NASA video, frame by frame.',
    compareGeneric: 'The calculated rate is compared with the published value for the same test. These cases belong to the development set.',
    test: 'TEST', relative: 'RELATIVE DIFFERENCE', dataLabel: 'DATA', frames: 'frames', comparisonSource: 'comparison source',
  },
  droplet: {
    index: '04 / DROPLET COMBUSTION', title: 'A DROPLET CHANGES SIZE AS IT BURNS.',
    intro: 'Three real FLEX droplet diameter files replayed in time. Droplet size follows the measured diameter; the flame halo is conceptual.',
    formula: 'D²(t) ≈ D₀² − K·t  (approximately linear segment)',
    note: 'This diagram does not show that all tests follow a straight line or end by extinction.',
    norm: 'D²(t) / D²(t≈0.3 s)', time: 'VIDEO TIME (s)', diameter: 'MEASURED DIAMETER', play: 'PLAY', pause: 'PAUSE', scrub: 'Replay time',
    fuels: { '20CAL13': 'HEPTANE · FLEX-007', '20CAL08': 'METHANOL / AIR · FLEX-001', '256F002': 'METHANOL · FLEX-010' } as Record<string, string>,
    loading: 'LOADING FLEX SERIES', error: 'The droplet series could not be loaded.',
    halo: 'FLAME HALO · CONCEPTUAL',
  },
  pipeline: {
    index: 'PROVENANCE PIPELINE', nodes: ['NASA PSI', 'VIDEO · TABLES · SENSORS', 'TEAM ANALYSIS', 'TO VALIDATE'],
    notes: ['Public records', 'Original source', 'Calculated', 'Potential application'],
  },
  loop: {
    index: '05 / AUTORESEARCH LOOP', title: 'ONE CHANGE. ONE MEASUREMENT. ONE DECISION.',
    intro: 'An agent proposes changes to a model, runs them under fixed rules and compares the result with previous attempts. It keeps verifiable improvements and documents discarded trials.',
    steps: ['PROPOSE', 'MODIFY', 'RUN', 'RECORD'], stepNotes: ['Formulate a concrete idea', 'Edit the only permitted file', 'Train and measure under fixed rules', 'Save the metric, code and decision'],
    decision: 'DID THE METRIC IMPROVE?', keep: 'KEEP', discard: 'DISCARD',
    example: 'A REAL EXAMPLE · ACME PSI-10', exampleFacts: [['ATTEMPTS', '12'], ['VALIDATION ERROR VS. BASELINE', '−59.5%'], ['HOLDOUT RMSE · 50 RECORDS', 'K']],
    disclaimer: 'AutoResearch is a computational search method; it does not observe the flame or establish a physical hypothesis on its own.',
  },
  footerWord: 'FLAME IN FREEFALL',
};
type FxCopy = typeof en;
const es: FxCopy = {
  gravity: {
    index: '01 / ¿POR QUÉ MICROGRAVEDAD?', title: 'LA MISMA LLAMA. SIN FLOTABILIDAD.',
    intro: 'La gravedad cambia cómo recibe oxígeno una llama. Cambia el régimen para ver la diferencia conceptual descrita en la base de conocimiento de BASS-II.',
    modes: ['1 g · TIERRA', 'μg · ÓRBITA', 'FLUJO BAJO · EXTINCIÓN'],
    mode: 'RÉGIMEN',
    panels: [
      { tag: 'PENACHO FLOTANTE', title: 'EN LA TIERRA, LOS GASES CALIENTES SUBEN', body: 'La flotabilidad crea un penacho ascendente que estira la llama hacia arriba. La luz amarilla-anaranjada es hollín incandescente.' },
      { tag: 'SIN PENACHO ASCENDENTE', title: 'EN ÓRBITA, LA LLAMA SE ENSANCHA', body: 'Sin flotabilidad no hay penacho ascendente. La llama es más gruesa, ancha y corta, con mayor separación de la superficie (difusión más flujo forzado). Se ve ovalada, hemisférica o circular.' },
      { tag: 'CERCA DE LA EXTINCIÓN', title: 'CON FLUJO BAJO, SE REDUCE Y SE APAGA', body: 'Con flujo opuesto bajo, la llama se acorta y se estrecha hasta volverse circular, azul, y extinguirse. En BASS-II esto ocurre entre 1 y 5 cm/s.' },
    ],
    colour: 'COLOR', colourNote: 'El azul es quimioluminiscencia (CH*, C₂*). El amarillo-anaranjado es hollín incandescente. Con flujo bajo se forma menos hollín y la llama se ve azul.',
    oxygen: 'APORTE DE O₂', oxygenModes: ['Arrastrado por el penacho', 'Difusión + flujo forzado', 'Limitado por difusión'],
    shape: 'FORMA', shapeModes: ['Gota alargada', 'Ovalada / hemisférica', 'Círculo pequeño → apagado'],
    diagram: 'ESQUEMA CONCEPTUAL / NO SON IMÁGENES DE NASA',
    source: 'FUENTE: BASE DE CONOCIMIENTO BASS-II · FORMA Y COLOR DE LA LLAMA EN μg (Link 2018; NASA TM §6.1.4)',
  },
  rail: {
    index: '02 / CINCO MISIONES', title: 'CINCO FENÓMENOS. CINCO REGISTROS VIVOS.', intro: 'Recorre el archivo con el scroll. Cada expediente muestra una cifra real de su evidencia exportada; los esquemas son conceptuales.',
    open: 'CONSULTAR EXPEDIENTE', drag: 'DESPLÁZATE PARA RECORRER →',
    facts: {
      acme: [['CASOS DEL MODELO', '236'], ['CONFIGURACIONES', 'NORMAL / INVERSA'], ['RMSE RESERVADO', 'K']],
      'bass-ii': [['ENSAYOS PROCESADOS', '83'], ['TASAS ESTACIONARIAS', '54'], ['COMPARACIONES PUBLICADAS', '25']],
      'saffire-ii': [['ENSAYOS ANALIZADOS', '9'], ['ENSAYO II-7 · 180 S', 'ppm'], ['SENSOR', 'CO₂ LOCAL']],
      'same-r': [['FOTOELÉCTRICO · CON FLUJO', '%'], ['IONIZACIÓN · CON FLUJO', '%'], ['ENSAYOS CON TELEMETRÍA', '47']],
      flex: [['ENSAYOS DOCUMENTADOS', '274'], ['FINALIZARON POR EXTINCIÓN', '186'], ['COMBUSTIBLES', 'METANOL / HEPTANO']],
    },
    notes: {
      acme: 'Quemador: combustible / ambiente: oxígeno — y la inversa. Esquema, no una llama medida.',
      'bass-ii': 'Un frente de llama cruzando una muestra. Las posiciones del borde provienen de video calibrado.',
      'saffire-ii': 'Lectura real de CO₂ absoluto del ensayo II-7. Respuesta local; no equivale a peligro total.',
      'same-r': 'El humo fresco envejece y se agrupa. Umbrales proxy del proyecto, no alarmas.',
      flex: 'Una gota se reduce mientras arde. Esquema conceptual, sin escala.',
    },
  },
  front: {
    index: '03 / DEL VIDEO A LA VELOCIDAD', title: 'MIRA AVANZAR UN FRENTE DE LLAMA REAL.',
    intro: 'Ensayo B1 · película PMMA. Desplázate para reproducir, fotograma a fotograma, las posiciones del borde frontal extraídas de video calibrado de NASA.',
    steps: [
      ['01 / OBSERVAR', 'El borde visible de la llama cambia de posición entre fotogramas.'],
      ['02 / MEDIR', 'Cada punto es una posición calculada a partir de un fotograma calibrado. Son mediciones, no pronósticos.'],
      ['03 / AJUSTAR', 'La pendiente durante un intervalo estable aproxima la velocidad de propagación V_f.'],
      ['04 / COMPARAR', 'En B1, la tasa calculada coincide de cerca con el valor publicado. Esta concordancia corresponde al desarrollo.'],
    ],
    time: 'TIEMPO DE VIDEO', edge: 'BORDE FRONTAL', measured: 'MEDIDA EN VIDEO', published: 'PUBLICADA', interval: 'INTERVALO ESTABLE',
    thickness: 'ESPESOR', flow: 'FLUJO INICIAL', oxygen: 'O₂ INICIAL', strip: 'POSICIÓN DEL FRENTE SOBRE LA MUESTRA (FRANJA ESQUEMÁTICA)',
    loading: 'CARGANDO SERIE B1', error: 'No se pudo cargar la serie B1.',
    warning: 'La extracción óptica puede incluir ruido. No equivale al registro directo de una regla física dentro del experimento.',
    introMulti: 'Elige uno de los tres ensayos con serie exportada. Desplázate para reproducir, fotograma a fotograma, las posiciones del borde frontal extraídas de video calibrado de NASA.',
    compareGeneric: 'La tasa calculada se compara con el valor publicado para el mismo ensayo. Estos casos pertenecen al conjunto de desarrollo.',
    test: 'ENSAYO', relative: 'DIFERENCIA RELATIVA', dataLabel: 'DATOS', frames: 'fotogramas', comparisonSource: 'fuente de comparación',
  },
  droplet: {
    index: '04 / COMBUSTIÓN DE GOTAS', title: 'UNA GOTA CAMBIA DE TAMAÑO AL ARDER.',
    intro: 'Tres archivos reales de diámetro de gotas FLEX reproducidos en el tiempo. El tamaño de la gota sigue el diámetro medido; el halo de llama es conceptual.',
    formula: 'D²(t) ≈ D₀² − K·t  (segmento aproximadamente lineal)',
    note: 'Este esquema no demuestra que todos los ensayos sigan una recta ni que terminen por extinción.',
    norm: 'D²(t) / D²(t≈0.3 s)', time: 'TIEMPO DE VIDEO (s)', diameter: 'DIÁMETRO MEDIDO', play: 'REPRODUCIR', pause: 'PAUSAR', scrub: 'Tiempo de reproducción',
    fuels: { '20CAL13': 'HEPTANO · FLEX-007', '20CAL08': 'METANOL / AIRE · FLEX-001', '256F002': 'METANOL · FLEX-010' },
    loading: 'CARGANDO SERIES FLEX', error: 'No se pudieron cargar las series de gotas.',
    halo: 'HALO DE LLAMA · CONCEPTUAL',
  },
  pipeline: {
    index: 'CADENA DE PROCEDENCIA', nodes: ['NASA PSI', 'VIDEO · TABLAS · SENSORES', 'ANÁLISIS DEL EQUIPO', 'A VALIDAR'],
    notes: ['Registros públicos', 'Fuente original', 'Calculado', 'Aplicación potencial'],
  },
  loop: {
    index: '05 / CICLO AUTORESEARCH', title: 'UN CAMBIO. UNA MEDICIÓN. UNA DECISIÓN.',
    intro: 'Un agente propone cambios a un modelo, los ejecuta bajo reglas fijas y compara el resultado con intentos anteriores. Conserva las mejoras verificables y documenta los ensayos descartados.',
    steps: ['PROPONER', 'MODIFICAR', 'EJECUTAR', 'REGISTRAR'], stepNotes: ['Formular una idea concreta', 'Editar el único archivo permitido', 'Entrenar y medir con reglas fijas', 'Guardar métrica, código y decisión'],
    decision: '¿MEJORÓ LA MÉTRICA?', keep: 'CONSERVAR', discard: 'DESCARTAR',
    example: 'UN EJEMPLO REAL · ACME PSI-10', exampleFacts: [['INTENTOS', '12'], ['ERROR DE VALIDACIÓN VS. LÍNEA BASE', '−59.5%'], ['RMSE RESERVADO · 50 REGISTROS', 'K']],
    disclaimer: 'AutoResearch es un método de búsqueda computacional; no observa la llama ni establece por sí solo una hipótesis física.',
  },
  footerWord: 'FLAME IN FREEFALL',
};
export const fxCopy: Record<Locale, FxCopy> = { en, es };
export type { FxCopy };
