import type { Locale } from '@/shared/i18n';

// 3D mission explorer copy. Facts: investigations/SAFFIRE (report + analysis JSON) and exported
// evidence. The vehicle, Earth and experiment layout are stylised and labelled as such.
const en = {
  meta: { title: 'SAFFIRE-II 3D Explorer · Los Espinosaurios', description: 'Fly around a stylised cargo spacecraft in orbit, open it, and ignite a real SAFFIRE-II test driven by measured data.' },
  eyebrow: 'S//L / 3D EXPLORER / NASA PSI-99', title: 'FIRE IN ORBIT · EXPLORER',
  intro: 'Fly to the spacecraft, slice it open, pull the experiment out and ignite one of the nine real SAFFIRE-II tests. Every number on screen comes from the mission records.',
  back: '← BACK TO MISSION CONTROL', loading: 'LOADING SPACECRAFT…', webgl: 'WebGL is not available in this browser.',
  objectives: 'MISSION OBJECTIVES', complete: 'COMPLETE',
  goals: {
    approach: 'Approach the spacecraft (zoom in)', inspect: 'Inspect a component (click a beacon)', open: 'Open the hull (cutaway or exploded view)',
    test: 'Choose a real test', ignite: 'Arm and ignite', spread: 'Watch the flame and its products', measure: 'Reach t = 180 s and read Δ CO₂',
  } as Record<string, string>,
  status: { idle: 'STANDBY', armed: 'BASELINE · T−', burning: 'IGNITION', done: 'RECORD COMPLETE', paused: 'PAUSED' },
  clock: 'T FROM IGNITION', utc: 'ELECTRICAL MARKER',
  controls: {
    test: 'TEST', ignite: 'ARM & IGNITE', pause: 'PAUSE', resume: 'RESUME', reset: 'RESET', speed: 'TIME',
    cut: 'HULL CUTAWAY', explode: 'EXPLODED VIEW', sun: 'SUN ANGLE', orbit: 'ORBIT SPEED', labels: 'BEACONS', autorotate: 'AUTO ORBIT CAM',
    views: { orbit: 'ORBIT', craft: 'SPACECRAFT', rack: 'EXPERIMENT', flame: 'FLAME' } as Record<string, string>,
  },
  keys: 'MOUSE: drag rotate · wheel zoom · right-drag pan · double-click focus   KEYS: W A S D orbit · Q E zoom · C cut · X explode · SPACE ignite/pause · R reset view',
  pip: 'EXPERIMENT CAM · LIVE', pipNote: 'Close-up inside the flow duct (schematic, enlarged)',
  co2: 'CO₂ SENSOR · REAL SERIES', reading: 'Reading', delta: 'Reading − baseline', final: 'Δ CO₂ at 180 s',
  outcome: 'DOCUMENTED OUTCOME', burn: 'Published burn', rate: 'Spread rate', none: 'not published', insignificant: 'insignificant',
  radar: 'ORBIT RADAR',
  parts: {
    cargo: ['CARGO MODULE', 'Stylised pressurised module. NASA ignited the SAFFIRE-II specimens inside an uncrewed Cygnus vehicle; the nine tests share one cabin history.'],
    service: ['SERVICE MODULE', 'Stylised propulsion and power section. Not part of the measurements.'],
    array: ['SOLAR ARRAY', 'Stylised fan-type solar array. Not part of the measurements.'],
    rack: ['EXPERIMENT · FLOW DUCT', 'Forced air flows over the specimen. Pre-ignition flow for this test: {flow} cm/s, {dir}. O₂ sensor {o2} %, {p} kPa.'],
    sample: ['SPECIMEN 29 × 5 cm', '{material}, {thickness} mm. Documented outcome: {outcome}.'],
    igniter: ['IGNITER', 'Commanded {power} W for {duration} s. The electrical marker defines t = 0 (not a verified optical ignition time).'],
    tc: ['PLUME THERMOCOUPLES ×6', 'Hottest sampled value in the first 180 s: {plume} °C. A sampled location, not the flame temperature.'],
    co2: ['CO₂ SENSOR', 'Local sensor. Team response: Δ = median [150, 180) s − median [−30, 0) s = {delta} ppm for this test.'],
    earth: ['EARTH', 'Stylised and not to scale.'],
  } as Record<string, [string, string]>,
  log: 'MISSION LOG',
  events: { armed: 'Armed · baseline window [−30, 0) s', ignition: 'Ignition marker · {utc} UTC', igniterOff: 'Igniter off ({power} W × {duration} s)', burnEnd: 'Published burn ends · {duration} s · {length} cm', noSpread: 'No sustained spread (published)', front: 'Front reaches 29 cm (published {rate} mm/s)', response: 'Response window [150, 180) s', delta: 'Δ CO₂ at 180 s = {delta} ppm' },
  disclaimer: 'Stylised vehicle and Earth, not to scale; the experiment is enlarged and its layout is schematic. Flame motion follows the published outcome, burn length and duration (only SIBAL has spread rates). CO₂ values are the real sensor series. No explosion is documented.',
  open3d: 'ENTER THE 3D EXPLORER', open3dNote: 'Fly, open the spacecraft and ignite a test',
};
type ExplorerCopy = typeof en;
const es: ExplorerCopy = {
  meta: { title: 'Explorador 3D SAFFIRE-II · Los Espinosaurios', description: 'Vuela alrededor de una nave de carga estilizada en órbita, ábrela y enciende un ensayo real de SAFFIRE-II con datos medidos.' },
  eyebrow: 'S//L / EXPLORADOR 3D / NASA PSI-99', title: 'FUEGO EN ÓRBITA · EXPLORADOR',
  intro: 'Vuela hasta la nave, córtala, extrae el experimento y enciende uno de los nueve ensayos reales de SAFFIRE-II. Cada número en pantalla proviene de los registros de la misión.',
  back: '← VOLVER AL CONTROL DE MISIÓN', loading: 'CARGANDO NAVE…', webgl: 'WebGL no está disponible en este navegador.',
  objectives: 'OBJETIVOS DE MISIÓN', complete: 'COMPLETADO',
  goals: {
    approach: 'Acércate a la nave (zoom)', inspect: 'Inspecciona un componente (clic en una baliza)', open: 'Abre el casco (corte o vista explotada)',
    test: 'Elige un ensayo real', ignite: 'Arma y enciende', spread: 'Observa la llama y sus productos', measure: 'Llega a t = 180 s y lee Δ CO₂',
  },
  status: { idle: 'EN ESPERA', armed: 'LÍNEA BASE · T−', burning: 'IGNICIÓN', done: 'REGISTRO COMPLETO', paused: 'EN PAUSA' },
  clock: 'T DESDE LA IGNICIÓN', utc: 'MARCADOR ELÉCTRICO',
  controls: {
    test: 'ENSAYO', ignite: 'ARMAR Y ENCENDER', pause: 'PAUSAR', resume: 'CONTINUAR', reset: 'REINICIAR', speed: 'TIEMPO',
    cut: 'CORTE DEL CASCO', explode: 'VISTA EXPLOTADA', sun: 'ÁNGULO DEL SOL', orbit: 'VELOCIDAD ORBITAL', labels: 'BALIZAS', autorotate: 'CÁMARA AUTOMÁTICA',
    views: { orbit: 'ÓRBITA', craft: 'NAVE', rack: 'EXPERIMENTO', flame: 'LLAMA' },
  },
  keys: 'RATÓN: arrastra para rotar · rueda para zoom · clic derecho para desplazar · doble clic para enfocar   TECLAS: W A S D orbitar · Q E zoom · C corte · X explotar · ESPACIO encender/pausar · R reiniciar vista',
  pip: 'CÁMARA DEL EXPERIMENTO · EN VIVO', pipNote: 'Primer plano dentro del ducto (esquemático, ampliado)',
  co2: 'SENSOR CO₂ · SERIE REAL', reading: 'Lectura', delta: 'Lectura − base', final: 'Δ CO₂ a 180 s',
  outcome: 'RESULTADO DOCUMENTADO', burn: 'Combustión publicada', rate: 'Tasa de propagación', none: 'no publicada', insignificant: 'insignificante',
  radar: 'RADAR ORBITAL',
  parts: {
    cargo: ['MÓDULO DE CARGA', 'Módulo presurizado estilizado. La NASA encendió las muestras de SAFFIRE-II dentro de una nave Cygnus sin tripulación; los nueve ensayos comparten una misma historia de cabina.'],
    service: ['MÓDULO DE SERVICIO', 'Sección de propulsión y energía estilizada. No forma parte de las mediciones.'],
    array: ['PANEL SOLAR', 'Panel solar tipo abanico estilizado. No forma parte de las mediciones.'],
    rack: ['EXPERIMENTO · DUCTO DE FLUJO', 'Aire forzado sobre la muestra. Flujo previo de este ensayo: {flow} cm/s, {dir}. Sensor O₂ {o2} %, {p} kPa.'],
    sample: ['MUESTRA 29 × 5 cm', '{material}, {thickness} mm. Resultado documentado: {outcome}.'],
    igniter: ['IGNITOR', 'Programado a {power} W durante {duration} s. El marcador eléctrico define t = 0 (no es un tiempo de ignición óptica verificado).'],
    tc: ['TERMOPARES DE PENACHO ×6', 'Valor máximo muestreado en los primeros 180 s: {plume} °C. Es una ubicación muestreada, no la temperatura de la llama.'],
    co2: ['SENSOR CO₂', 'Sensor local. Respuesta del equipo: Δ = mediana [150, 180) s − mediana [−30, 0) s = {delta} ppm en este ensayo.'],
    earth: ['TIERRA', 'Estilizada y sin escala.'],
  },
  log: 'BITÁCORA DE MISIÓN',
  events: { armed: 'Armado · ventana base [−30, 0) s', ignition: 'Marcador de ignición · {utc} UTC', igniterOff: 'Ignitor apagado ({power} W × {duration} s)', burnEnd: 'Termina la combustión publicada · {duration} s · {length} cm', noSpread: 'Sin propagación sostenida (publicado)', front: 'El frente llega a 29 cm ({rate} mm/s publicada)', response: 'Ventana de respuesta [150, 180) s', delta: 'Δ CO₂ a 180 s = {delta} ppm' },
  disclaimer: 'Nave y Tierra estilizadas, sin escala; el experimento está ampliado y su disposición es esquemática. La llama sigue el resultado, la longitud y la duración publicadas (solo SIBAL tiene tasas de propagación). Los valores de CO₂ son la serie real del sensor. No hay explosión documentada.',
  open3d: 'ENTRAR AL EXPLORADOR 3D', open3dNote: 'Vuela, abre la nave y enciende un ensayo',
};
export const explorerCopy: Record<Locale, ExplorerCopy> = { en, es };
export type { ExplorerCopy };
