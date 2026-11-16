export type Locale = 'en' | 'es';

const es = {
  navigation: 'NAVEGACIÓN', menuResearch: 'EXPEDIENTES NASA PSI', pageLabel: 'PÁGINA',
  nav: ['INICIO', 'INVESTIGACIONES', 'METODOLOGÍA', 'EQUIPO'], menu: 'MENÚ', close: 'CERRAR', explore: 'EXPLORAR', pages: 'PÁGINAS', language: 'IDIOMA', skip: 'Saltar al contenido',
  desktopEyebrow: 'S//L / EXPEDIENTES CIENTÍFICOS   ·   MICROGRAVEDAD', heroLines: ['LA FÍSICA DE', 'LAS LLAMAS', 'SIN GRAVEDAD.'],
  hero: 'LA FÍSICA DE LAS LLAMAS SIN GRAVEDAD.', intro: 'Exploramos investigaciones de NASA sobre combustión, propagación de llamas y detección de humo en microgravedad. Aquí encontrarás los datos, su interpretación y lo que todavía queda por descubrir.',
  view: 'VER INVESTIGACIONES', read: 'CÓMO LEER LOS DATOS', five: '05 INVESTIGACIONES', archive: 'ARCHIVO CIENTÍFICO', micro: 'MICROGRAVEDAD', emblem: 'FIG. 01 / IDENTIDAD LOS ESPINOSAURIOS',
  archiveIndex: '01 / EXPLORA EL ARCHIVO NASA', archiveTitle: 'CINCO FENÓMENOS. UN ARCHIVO.', archiveIntro: 'Consulta las cinco investigaciones de NASA sobre combustión, propagación de llamas, detección de humo y extinción en microgravedad.',
  compactArchiveIntro: 'Explora las preguntas, las condiciones experimentales y los resultados de cada estudio. Los esquemas y las mediciones se identifican por separado.', studies: '05 ESTUDIOS / NASA PSI',
  guideIndex: '02 / UNA GUÍA PARA LEER LOS DATOS', guideTitle: 'DATOS. CÁLCULOS. PROPUESTAS.', guideLines: ['DATOS.', 'CÁLCULOS.', 'PROPUESTAS.'],
  guideIntro: 'No todo lo que aparece en una gráfica es una medición directa. Señalamos de dónde viene cada resultado y hasta dónde llega su interpretación.', units: 'SIEMPRE CON UNIDADES Y FUENTES',
  evidence: [
    { title: 'FUENTE ORIGINAL', body: 'Registros, videos y tablas publicados por NASA PSI.', compact: 'Registros, videos y tablas publicados por NASA PSI.', badge: 'FUENTE NASA' },
    { title: 'ANÁLISIS DEL EQUIPO', body: 'Cálculos y modelos elaborados a partir de esos registros.', compact: 'Cálculos y modelos elaborados a partir de los registros.', badge: 'CALCULADO' },
    { title: 'APLICACIÓN POTENCIAL', body: 'Usos que podrían investigarse, pero aún requieren validación.', compact: 'Posibilidades que todavía requieren validación.', badge: 'A VALIDAR' },
  ],
  impactIndex: '03 / ¿PARA QUÉ PUEDE SERVIR?', impactTitle: 'ENTENDER PARA SEGUIR INVESTIGANDO.', impactIntro: 'Los hallazgos pueden orientar nuevas preguntas sobre combustión y seguridad espacial. No significan que un sistema ya esté validado para su uso.',
  impacts: [
    { label: 'A / COMBUSTIÓN', title: 'CONDICIONES DE LLAMA', body: 'Analizar mezclas, presiones, combustión de gotas y condiciones de extinción en microgravedad.' },
    { label: 'B / MATERIALES', title: 'PROPAGACIÓN Y VENTILACIÓN', body: 'Estudiar cómo avanzan las llamas y cómo responden los materiales cuando cambia el aire.' },
    { label: 'C / INSTRUMENTACIÓN', title: 'SENSORES DE HUMO', body: 'Investigar métodos complementarios de detección bajo diferentes regímenes de transporte.' },
  ], impactStatus: 'ESTADO: POSIBILIDADES DE INVESTIGACIÓN / NO APLICACIONES CERTIFICADAS',
  methodIndex: '04 / CÓMO ANALIZAMOS', methodTitle: 'CÓMO ANALIZAMOS LOS DATOS.', methodIntro: 'El equipo registra preguntas, desarrolla análisis y documenta sus resultados. Cada expediente distingue las fuentes originales de los cálculos y de las hipótesis por validar.', methodSteps: 'PROPONER / EVALUAR / DOCUMENTAR', methodAction: 'VER METODOLOGÍA',
  footerIntro: 'Archivo de divulgación científica basado en datos públicos de NASA Physical Sciences Informatics (PSI). Los análisis y las interpretaciones del equipo se distinguen de sus fuentes originales.', footerData: 'DATOS NASA PSI', edition: 'EDICIÓN 2026 / FIN DE ARCHIVO',
  compactFooter: 'Los datos originales y las interpretaciones del equipo se distinguen por su procedencia.', mobile: 'MÓVIL', tablet: 'TABLETA', files: '02 / EXPEDIENTES', interpretation: '03 / INTERPRETACIÓN', open: 'CONSULTAR EXPEDIENTE',
  studiesList: [
    { slug: 'acme', psi: 'PSI-10 / ACME', title: 'CONDICIONES DE LLAMAS', question: '¿Cómo influyen las condiciones de ensayo en las llamas normales e inversas?', tags: 'FÍSICA DE COMBUSTIÓN / TAD CALCULADA' },
    { slug: 'bass-ii', psi: 'PSI-25 / BASS-II', title: 'LLAMAS SOBRE MATERIALES', question: '¿Cómo avanza una llama sobre una superficie y qué ocurre cuando cambia el flujo de aire?', tags: 'VIDEO / PROPAGACIÓN / MATERIALES' },
    { slug: 'saffire-ii', psi: 'PSI-99 / SAFFIRE-II', title: 'COMBUSTIÓN Y SENSORES', question: '¿Qué registran los sensores cuando se ensayan materiales combustibles en el espacio?', tags: 'RESPUESTA LOCAL DE CO₂ / MATERIALES' },
    { slug: 'same-r', psi: 'PSI-101 / SAME-R', title: 'HUMO Y DETECCIÓN', question: '¿Por qué cambian las partículas y por qué dos detectores responden de manera diferente?', tags: 'AEROSOLES / DOS PRINCIPIOS DE SENSOR' },
    { slug: 'flex', psi: 'PSI-69 / FLEX', title: 'GOTAS Y EXTINCIÓN DE LLAMAS', question: '¿Cómo arde una gota de combustible y cuándo se extingue su llama en microgravedad?', tags: 'GOTAS DE COMBUSTIBLE / TIEMPO / TASA DE COMBUSTIÓN' },
  ],
};
const en: typeof es = {
  navigation: 'NAVIGATION', menuResearch: 'NASA PSI RECORDS', pageLabel: 'PAGE',
  nav: ['HOME', 'RESEARCH', 'METHODOLOGY', 'TEAM'], menu: 'MENU', close: 'CLOSE', explore: 'EXPLORE', pages: 'PAGES', language: 'LANGUAGE', skip: 'Skip to content',
  desktopEyebrow: 'S//L / SCIENTIFIC RECORDS   ·   MICROGRAVITY', heroLines: ['THE PHYSICS OF', 'FLAMES', 'WITHOUT GRAVITY.'], hero: 'THE PHYSICS OF FLAMES WITHOUT GRAVITY.',
  intro: 'We explore NASA research on combustion, flame spread and smoke detection in microgravity. Discover the data, their interpretation and what remains to be understood.',
  view: 'EXPLORE RESEARCH', read: 'HOW TO READ THE DATA', five: '05 INVESTIGATIONS', archive: 'SCIENTIFIC ARCHIVE', micro: 'MICROGRAVITY', emblem: 'FIG. 01 / LOS ESPINOSAURIOS IDENTITY',
  archiveIndex: '01 / EXPLORE THE NASA ARCHIVE', archiveTitle: 'FIVE PHENOMENA. ONE ARCHIVE.', archiveIntro: 'Explore five NASA investigations into combustion, flame spread, smoke detection and extinguishment in microgravity.', compactArchiveIntro: 'Explore the questions, experimental conditions and findings of each study. Diagrams and measurements are identified separately.', studies: '05 STUDIES / NASA PSI',
  guideIndex: '02 / A GUIDE TO READING THE DATA', guideTitle: 'DATA. CALCULATIONS. PROPOSALS.', guideLines: ['DATA.', 'CALCULATIONS.', 'PROPOSALS.'], guideIntro: 'Not everything in a chart is a direct measurement. We identify the source of each result and the limits of its interpretation.', units: 'ALWAYS WITH UNITS AND SOURCES',
  evidence: [
    { title: 'ORIGINAL SOURCE', body: 'Records, videos and tables published by NASA PSI.', compact: 'Records, videos and tables published by NASA PSI.', badge: 'NASA SOURCE' },
    { title: 'TEAM ANALYSIS', body: 'Calculations and models developed from those records.', compact: 'Calculations and models developed from the records.', badge: 'CALCULATED' },
    { title: 'POTENTIAL APPLICATION', body: 'Uses that could be investigated but still require validation.', compact: 'Possibilities that still require validation.', badge: 'TO VALIDATE' },
  ], impactIndex: '03 / WHAT COULD THIS INFORM?', impactTitle: 'UNDERSTAND. KEEP INVESTIGATING.', impactIntro: 'Findings can inform new questions about combustion and space safety. They do not mean a system has been validated for use.',
  impacts: [
    { label: 'A / COMBUSTION', title: 'FLAME CONDITIONS', body: 'Analyze mixtures, pressures, droplet combustion and extinguishment conditions in microgravity.' },
    { label: 'B / MATERIALS', title: 'SPREAD AND VENTILATION', body: 'Study how flames spread and how materials respond when airflow changes.' },
    { label: 'C / INSTRUMENTATION', title: 'SMOKE SENSORS', body: 'Investigate complementary detection methods under different transport regimes.' },
  ], impactStatus: 'STATUS: RESEARCH POSSIBILITIES / NOT CERTIFIED APPLICATIONS',
  methodIndex: '04 / HOW WE ANALYZE', methodTitle: 'HOW WE ANALYZE THE DATA.', methodIntro: 'The team records questions, develops analyses and documents results. Every record distinguishes original sources from calculations and hypotheses awaiting validation.', methodSteps: 'PROPOSE / EVALUATE / DOCUMENT', methodAction: 'VIEW METHODOLOGY',
  footerIntro: 'A science communication archive based on public NASA Physical Sciences Informatics (PSI) data. Team analyses and interpretations are distinguished from their original sources.', footerData: 'NASA PSI DATA', edition: '2026 EDITION / END OF ARCHIVE', compactFooter: 'Original data and team interpretations are distinguished by their provenance.', mobile: 'MOBILE', tablet: 'TABLET', files: '02 / RECORDS', interpretation: '03 / INTERPRETATION', open: 'OPEN RESEARCH RECORD',
  studiesList: [
    { slug: 'acme', psi: 'PSI-10 / ACME', title: 'FLAME CONDITIONS', question: 'How do experimental conditions influence normal and inverse flames?', tags: 'COMBUSTION PHYSICS / CALCULATED TAD' },
    { slug: 'bass-ii', psi: 'PSI-25 / BASS-II', title: 'FLAMES OVER MATERIALS', question: 'How does a flame spread over a surface, and what happens when airflow changes?', tags: 'VIDEO / FLAME SPREAD / MATERIALS' },
    { slug: 'saffire-ii', psi: 'PSI-99 / SAFFIRE-II', title: 'COMBUSTION AND SENSORS', question: 'What do sensors record when combustible materials are tested in space?', tags: 'LOCAL CO₂ RESPONSE / MATERIALS' },
    { slug: 'same-r', psi: 'PSI-101 / SAME-R', title: 'SMOKE AND DETECTION', question: 'Why do particles change, and why do two detectors respond differently?', tags: 'AEROSOLS / TWO SENSOR PRINCIPLES' },
    { slug: 'flex', psi: 'PSI-69 / FLEX', title: 'DROPLETS AND FLAME EXTINCTION', question: 'How does a fuel droplet burn, and when does its flame go out in microgravity?', tags: 'FUEL DROPLETS / TIME / BURNING RATE' },
  ],
};
export const dictionaries = { en, es };
export const pagePaths = ['', 'research/', 'methodology/', 'team/'];
