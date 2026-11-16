# Spinosaurios Research Hub — plan maestro de implementación

La prioridad será **fidelidad a Figma → experiencia e interacción → integración científica**. Primero se entregará Inicio completo para revisión visual; después se extenderá el sitio y se conectarán los laboratorios.

**Estado de esta entrega:** investigación y planificación completadas, sin modificar el repositorio. Los cinco documentos siguientes quedan especificados para su materialización; Plan Mode impide escribirlos ahora. Los archivos se redactarán en inglés, conforme a `CLAUDE.md`; el sitio tendrá contenido completo en inglés y español.

## 1. `docs/MASTER_IMPLEMENTATION_PLAN.md`

### Estado real del repositorio

| Elemento | Resultado verificado |
|---|---|
| Rama | `feature/frontend`, siguiendo `origin/feature/frontend` |
| HEAD | `0b232fd` |
| Árbol de trabajo | Limpio |
| Frontend nuevo | No existe |
| Dependencias frontend | Sin `package.json`, lockfile Node ni `node_modules` |
| Herramientas disponibles | Node, npm, pnpm, Python y uv |
| Investigaciones | `ACME`, `BASS-II`, `SAFFIRE`, `SAME`, `flex` |
| Exportador existente | `investigations/export_predictions.py` |
| Recursos existentes | Figuras científicas PNG/JPG y tablas; sin fuentes WOFF2 ni SVG frontend preparados |
| Instrucciones | `CLAUDE.md`; instrucciones específicas de ACME y BASS-II al consultar esas investigaciones |

Las descripciones antiguas del README que llaman a FLEX un placeholder están desactualizadas respecto a sus archivos reales. No se recuperará código frontend desde el historial.

### Arquitectura acordada

Crear una aplicación independiente bajo `frontend/`, con Next.js App Router, React, TypeScript estricto y Tailwind CSS. Usar versiones estables compatibles y registrar las versiones resueltas en un único `package-lock.json`; npm será el gestor del frontend.

| Directorio | Responsabilidad |
|---|---|
| `app/` | Rutas Next, layouts, metadatos y parámetros estáticos; adaptadores delgados |
| `src/_app/` | Estilos globales, fuentes, configuración y proveedores |
| `src/_pages/` | Composición de Inicio, catálogo, metodología, equipo y cinco páginas científicas |
| `src/widgets/` | Cabecera, pie, menú y bloques compuestos reutilizados |
| `src/features/` | Cambio de idioma, filtros y controles de exploración |
| `src/entities/` | Investigaciones, contratos científicos y acceso a los JSON publicados |
| `src/shared/` | Componentes visuales básicos, utilidades, i18n, tokens y recursos |

Las capas importarán únicamente desde capas inferiores. Cada slice compartido tendrá una entrada pública pequeña. Se podrán mantener componentes específicos dentro de cada página: **no habrá una plantilla universal que fuerce los cinco dashboards a ser idénticos**. Esta separación sigue la [guía FSD para Next.js](https://feature-sliced.design/docs/guides/tech/with-nextjs).

El contenido editorial se generará como HTML estático. Menús, filtros, gráficos y laboratorios serán islas cliente pequeñas. No se añadirá una biblioteca global de estado.

### Rutas e idiomas

Usar los mismos segmentos técnicos en ambos idiomas:

- `/en/` y `/es/`
- `/{locale}/research/`
- `/{locale}/methodology/`
- `/{locale}/team/`
- `/{locale}/research/{slug}/`

Slugs: `saffire-ii`, `acme`, `bass-ii`, `same-r`, `flex`.

Decisiones:

- Inglés predeterminado; la raíz tendrá una entrada estática con enlace y redirección cliente a `/en/`, sin depender de redirecciones del servidor.
- `generateStaticParams()` enumerará ambos idiomas y las cinco investigaciones.
- Diccionarios versionados con claves tipadas y estructura equivalente para EN/ES.
- Traducir navegación, contenido editorial, etiquetas, accesibilidad, estados, títulos y metadatos.
- Mantener originales los identificadores, códigos de material, números, unidades y documentos científicos.
- El selector conservará página, hash y parámetros compatibles; la URL determinará el idioma.
- Selector visible en la cabecera de escritorio y dentro del menú móvil/tableta, decisión confirmada por el usuario.
- `lang`, canonical y alternativas de idioma correctos en cada página.
- No utilizar middleware ni la configuración de i18n del Pages Router.

### Responsabilidad de las bibliotecas

| Tecnología | Uso exclusivo |
|---|---|
| Tailwind CSS | Layout responsive y estilos derivados de tokens |
| shadcn/ui | Primitivas accesibles para menú, diálogo, pestañas, selección y campos; apariencia adaptada a Figma |
| Material UI | Reservado para un slider calibrado si una pantalla implementada lo necesita; sin segundo sistema de botones, tablas o navegación |
| Motion for React | Entradas, salidas, menú, revelados y cambios de estado de interfaz |
| Motion AI Kit | Herramientas del agente para consultar documentación y preparar animaciones; no dependencia de ejecución |
| Anime.js | Secuencias explicativas de símbolos científicos, aisladas de Motion y de los datos |
| Easing Editor | Preparar curvas reutilizables; sin editor incorporado al sitio |
| Apache ECharts | Gráficos científicos interactivos y sus transiciones |

Material UI, Anime.js y ECharts se incorporarán cuando llegue su tarea concreta. Inicio no cargará estas bibliotecas.

Motion AI Kit es una [herramienta para agentes](https://motion.dev/docs/ai-kit); ECharts permite [importar únicamente los módulos utilizados](https://echarts.apache.org/handbook/en/basics/import/). No se requieren componentes premium de Motion.

### GitHub Pages

Configurar desde la primera entrega:

- `output: "export"`.
- `trailingSlash: true`.
- `basePath: "/los-espinosaurios-flame-in-freefall"`.
- Imágenes locales sin optimizador de servidor.
- Fuentes locales mediante `next/font/local`, con sus licencias.
- `next/link` con rutas internas sin duplicar el prefijo.
- Una única utilidad para prefijar URLs de archivos públicos, JSON y descargas.
- Sin `assetPrefix` adicional, rewrites, Server Actions, endpoints dinámicos ni servicios externos necesarios para navegar.
- JSON científicos cargados bajo demanda, fuera de los imports cliente iniciales.

La exportación estática requiere enumerar rutas dinámicas y excluye funcionalidades dependientes de servidor. Véase [Next.js Static Exports](https://nextjs.org/docs/app/guides/static-exports). El prefijo se aplica automáticamente a los enlaces Next, pero requiere tratamiento explícito en recursos públicos, según [basePath](https://nextjs.org/docs/app/api-reference/config/next-config-js/basePath).

La futura acción de publicación construirá desde un checkout limpio, verificará datos y rutas, y publicará únicamente `frontend/out/`. Su creación corresponde al cierre de implementación; ejecutar el despliegue requerirá autorización posterior.

### Tareas ordenadas y dependencias

| ID | Responsable | Entrega | Dependencia y verificación |
|---|---|---|---|
| V1 | Frontend | Configuración mínima, recursos, cabecera, Inicio completo, EN/ES y Motion inicial | Revisión visual a 390/768/1440; typecheck y build |
| D1 | Datos | Recuperación reproducible de derivados ACME y contratos de publicación | Independiente de V1; hashes y exportador |
| V2 | Frontend | Catálogo con filtros funcionales | Aprobación visual de V1 |
| V3 | Frontend | Metodología y Equipo | Componentes aprobados de V1/V2 |
| D2 | Datos | JSON por investigación, series y procedencia | D1 y contrato científico |
| V4 | Frontend | SAFFIRE-II completo | D2; validación visual de sus tres tamaños |
| V5 | Frontend | ACME completo | D2; predicciones de validación separadas del holdout |
| V6 | Frontend | BASS-II completo | D2; métricas históricas y series disponibles |
| V7 | Frontend | SAME-R completo | D2; escenarios guardados y etiquetas proxy |
| V8 | Frontend | FLEX completo | D2; casos guardados y trayectorias originales |
| L1 | Frontend + Datos | Laboratorios funcionales | Página correspondiente revisada y datos verificados |
| R1 | Coordinador | Revisión final, optimización y workflow preparado | Todas las páginas y laboratorios cerrados |

V1 incluirá destinos estáticos mínimos para los enlaces aún pendientes: encabezado correcto y estado traducido de próxima entrega. No mostrarán resultados simulados ni contarán como páginas terminadas.

Después de cada página se solicitará revisión visual al usuario. Mientras espera esa revisión, el agente podrá avanzar en datos u otra tarea independiente.

### Política de verificación

- No ejecutar suites durante cambios de texto, espaciado o tokens.
- Ejecutar typecheck y build al cerrar cada hito.
- Revisar manualmente la página completa en sus tres tamaños y ambos idiomas.
- Probar con teclado menú, foco, controles, selector de idioma y estados de error.
- Añadir pruebas pequeñas únicamente para transformación científica, selección delicada o inferencia.
- Antes de publicar: comprobación completa de integridad, pruebas científicas pertinentes, build limpio, rutas directas, recursos con prefijo y revisión de rendimiento.

## 2. `docs/FIGMA_SPEC.md`

### Autoridad y cobertura

Fuente: [Spinosaurios Research Hub](https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub).

Se consultaron los **27 frames principales**, se obtuvieron sus capturas y se inspeccionaron Foundations, Components, Assets, Patterns y prototipos de navegación.

Cada frame manda en su tamaño, decisión confirmada. Las variantes responsive cambian también el contenido; no son versiones escaladas del escritorio.

| Página | Desktop: ID / alto | Mobile: ID / alto | Tablet: ID / alto |
|---|---|---|---|
| Inicio | `215:2` / 3158 | `385:3` / 2556 | `385:137` / 1848 |
| Investigaciones | `228:23` / 4200 | `385:65` / 2601 | `385:202` / 1947 |
| Metodología | `244:43` / 5560 | `386:2` / 2079 | `386:50` / 1720 |
| Equipo | `250:43` / 3440 | `386:98` / 2157 | `386:152` / 1574 |
| SAFFIRE-II | `320:27` / 6640 | `386:209` / 4244 | `386:382` / 3673 |
| ACME | `326:27` / 7750 | `386:554` / 4256 | `386:680` / 3503 |
| BASS-II | `332:27` / 7859 | `386:805` / 4749 | `386:985` / 3963 |
| SAME-R | `338:27` / 8469 | `386:1164` / 4801 | `386:1335` / 3985 |
| FLEX | `346:27` / 8119 | `386:1505` / 3678 | `386:1619` / 3065 |

Anchos originales: desktop 1440, mobile 390, tablet 768. Los altos son referencias de composición, no alturas CSS fijas.

Las copias `[B]` y posteriores representan estados interactivos. Los frames marcados `ARCHIVO` y las exploraciones anteriores no son objetivos de implementación.

### Tokens extraídos

| Función | Valor |
|---|---|
| Canvas / ground / raised / panel | `#020305` / `#05080D` / `#0B1119` / `#0F1720` |
| Texto principal / secundario | `#F2F3ED` / `#8C9EAE` |
| Sistema / información | `#228BDF` / `#77C3ED` |
| Restricción / aceptado / descartado | `#C81936` / `#87B9A4` / `#5C6873` |
| Borde desktop / ejes | `#2C3A47` / `#1B2632` |
| Bordes responsive | `#203040`, `#294050` |
| Texto responsive | `#9DAFBE`, `#AFC0CD` |
| Acento rojo responsive | `#FF667A` |

No sustituir las diferencias responsive por un único color “aproximado”.

Tipografía:

- **Oxanium 700/800:** títulos, cifras y expedientes.
- **Chakra Petch 400/500:** explicación científica y lectura.
- **IBM Plex Mono 400/500/700:** metadatos, navegación, unidades y controles.
- Desktop Inicio: hero 70–71 px; títulos de sección 30–44 px; cuerpo 17–21 px.
- Desktop dashboards: títulos principales entre 61 y 72 px; encabezados de sección 35–40 px; cuerpo 16–21 px.
- Responsive: encabezados 23/33 px, fichas 20/28 px, cuerpo 16/23 y 15/21 px, etiquetas 12/17 px.
- Conservar subíndices, superíndices, símbolos y capitalización.

Geometría:

- Escala base de Foundations: 4, 8, 12, 16, 24, 32, 48, 64 y 96 px.
- Separadores de 1 px; radios entre 0 y 4 px.
- Desktop: contenido máximo de 1280 px, margen nominal de 80 px.
- Mobile: padding 20 px y contenido nominal de 350 px.
- Tablet: padding 32 px y contenido nominal de 704 px.
- Inicio responsive usa separación vertical de 22 px; las otras páginas, generalmente 24 px.
- Fichas responsive: padding 16 px y separación interior de 10–12 px.
- Breakpoints de implementación: móvil `<768`, tableta `768–1199`, escritorio `≥1200`.
- Entre frames, interpolar anchuras sin reducir el texto científico ni introducir scroll horizontal global.

### Inicio: composición exacta de la primera entrega

**Desktop**, en orden:

| Bloque | Y / alto |
|---|---|
| Sistema y navegación | 46 / 100 |
| Hero e identidad científica | 148 / 808 |
| Acceso al archivo | 994 / 350 |
| Cómo leer resultados | 1370 / 570 |
| Aplicaciones y preguntas abiertas | 1972 / 527 |
| Método de análisis | 2534 / 293 |
| Fuentes y cierre | 2869 / 250 |

Detalles que determinan la semejanza:

- Ejes verticales exteriores en x≈42 y x≈1398; señales roja y azul superiores.
- Cabecera con marca a la izquierda y cuatro enlaces a la derecha; indicador azul en Inicio.
- Hero con título de tres líneas: “LA FÍSICA DE / LAS LLAMAS / SIN GRAVEDAD.”
- Columna tipográfica izquierda y emblema original a la derecha.
- Emblema `215:32`: aproximadamente 408×408, x865/y353 global.
- Círculo externo `215:38`: 485×485, x838/y319 global.
- Círculo interior `215:39`: 412×412, x874/y356 global.
- Acciones de 304×52 px, separadas 16 px.
- Guía de lectura con columna editorial izquierda y tres filas de evidencia a la derecha.
- Aplicaciones en tres columnas; bloque metodológico ancho; pie editorial.

**Mobile/tablet**, en orden:

1. Marca y botón Menú.
2. Línea azul.
3. Acceso rápido: un enlace en móvil; cuatro enlaces en tableta.
4. Identificador de página.
5. Hero textual.
6. Línea roja.
7. Introducción del archivo.
8. Cinco fichas: ACME, BASS-II, SAFFIRE-II, SAME-R y FLEX.
9. Guía “DATOS. CÁLCULOS. PROPUESTAS.”
10. Tres fichas de interpretación.
11. Cierre compacto.

No aparece el emblema desktop. Tampoco se trasladan automáticamente las secciones desktop de aplicaciones y metodología.

Las cinco fichas forman una columna en móvil y dos columnas en tableta; la quinta conserva el ancho de una columna.

### Otras páginas editoriales

| Página | Orden desktop | Adaptación responsive |
|---|---|---|
| Investigaciones | Portada → filtros → cinco expedientes → matriz de variables/unidades → procedencia → pie | Filtros repartidos en filas; fichas a una/dos columnas; comparación resumida |
| Metodología | AutoResearch → persona/agente/evaluación → ciclo → original frente a adaptación → cinco protocolos → ejemplo ACME → límites → referencias | Flujo y comparaciones convertidos en bloques verticales |
| Equipo | Presentación → cinco investigadores → reglas compartidas → créditos | Una columna móvil; dos columnas tablet |

Catálogo:

- Filtros: Todos, Combustión, Propagación, Extinción y Humo/Sensores.
- Cada expediente puede pertenecer a varias categorías.
- Conservar orden original al filtrar y mostrar cantidad de resultados.
- Filtrar contenido existente; no producir rankings científicos.
- Desktop utiliza filas editoriales con una representación científica lateral.

Equipo:

- Josué Guevara / `PonchoDeFrutas` / ACME.
- Carbonell Castillo / `Carbonell-Castillo` / BASS-II.
- Natalia / `nxz7` / SAFFIRE-II.
- `ELFBIBv` / SAME-R.
- Diego Cali / `DiegoCali` / FLEX.

Conservar las tarjetas de iniciales y enlaces originales; no inventar retratos ni atribuir autoría de experimentos NASA al equipo.

### Dashboards: diferencias obligatorias

Todos contienen hero, indicadores, explicación, evidencia, validación, laboratorio, registros y límites, pero conservan composiciones propias.

| Investigación | Secuencia específica y gráficos | Controles del diseño |
|---|---|---|
| SAFFIRE-II | CO₂ de nueve ensayos; ventanas de referencia/respuesta; paridad y error; respuesta del modelo; tabla | Silicone/otros; flujo 20, 22, 24.9 cm/s; restaurar |
| ACME | Llama normal/inversa; fracción ambiental frente a Tad; 52 predicciones; restricciones de entradas; laboratorio; tabla | Normal/Inverse; tres fracciones ambientales; restaurar |
| BASS-II | Frente conceptual; tasas extraídas/publicadas; trayectoria B1/M1; métricas por horizonte; laboratorio; registros | B1/M1; horizontes 1, 5, 10 s; restaurar |
| SAME-R | Aerosol reciente/envejecido; tamaños por material; detectores con/sin flujo; paridad; escenarios; tabla | Kapton/Lampwick; flujo/sin flujo; 38/566 s; restaurar |
| FLEX | Gota conceptual; tres trayectorias reales; desenlaces por combustible; paridad; casos guardados; tabla | Methanol/Heptane; presets O₂ 34/30/21%; restaurar |

Referencias verticales desktop para las secciones numeradas:

- SAFFIRE-II: 846, 1768, 2398, 3230, 4797, 5703.
- ACME: 816, 1480, 2475, 3455, 4152, 5947, 6797.
- BASS-II: 827, 1497, 2511, 3473, 4464, 5908, 6841.
- SAME-R: 828, 1510, 2488, 3485, 4488, 6472, 7435.
- FLEX: 816, 1465, 2465, 3496, 4470, 6297, 7081.

Indicadores desktop: cuatro columnas nominales de 302 px, con gaps de 24 px. Las secciones científicas suelen colocar gráfico ancho a la izquierda e interpretación a la derecha. Los laboratorios separan controles y resultados.

Los frames responsive utilizan gráficos simplificados, fichas y registros resumidos; no deben recibir automáticamente todos los paneles desktop.

### Componentes, estados y navegación

| Componente Figma | Contrato |
|---|---|
| Action Button `154:461` | Primary/Secondary/Quiet/Restricted × Default/Hover/Disabled |
| Signal Badge `154:400` | Source/Calculated/Model/Proxy/Verified/Draft |
| Combobox `155:472` | Closed/Focused/Expanded/Disabled |
| Calibrated Slider `155:613` | Single/Range × Default/Focused/Disabled |
| Numeric Input `156:595` | Default/Focused/Invalid/Disabled |
| Display Toggle `156:617` | Off/On/Disabled |
| View Tab `156:628` | Active/Idle/Disabled |
| Parameter Snapshot `122:308` | Lectura fija; no convertirla en campo editable |

- Botón editorial nominal: 304×52 px.
- Badge nominal: 214×38 px.
- Menú: frames `389:2` y `389:51`; páginas principales y cinco investigaciones.
- Aviso científico: `392:2` y `392:23`; estados activo, disponible, no disponible e inválido.
- En producción, el aviso explicará la capacidad real del laboratorio; no conservará mensajes exclusivos del prototipo Figma.
- Las pestañas de sección navegan a anclas; los controles de laboratorio actualizan estado local, sin navegar entre copias del dashboard.
- Menú con cierre, Escape, gestión y retorno del foco, y scroll interno en pantallas bajas.

### Recursos y aceptación visual

Descargar los SVG originales devueltos por MCP y conservar su relación con el nodo, dimensiones, destino y uso en una tabla dentro de esta especificación. Para Inicio: emblema y ambos círculos son obligatorios.

Conservar los símbolos orbitales, retículas, calibraciones y esquemas originales donde aparezcan. Las curvas o puntos que representan resultados se construirán con datos comprobados; un SVG ilustrativo no se convertirá en evidencia científica.

Las URLs temporales MCP no formarán parte del sitio. Las capturas son referencias de revisión, nunca fondos utilizados para imitar páginas.

La revisión de cada página comprobará composición completa, orden, recursos, proporciones, fuentes, alineación, controles y pie. En español se comparará directamente con Figma; en inglés se admitirán cambios naturales de salto de línea, conservando jerarquía y anchuras. No se aceptarán recortes de texto, recursos sustituidos ni resultados inventados.

## 3. `docs/MOTION_SPEC.md`

La geometría en reposo coincidirá con Figma. Foundations define respuesta de **120 ms**, transición de **220 ms** y barrido de **500 ms**. Los prototipos responsive utilizan disolución de aproximadamente **170 ms**.

Curvas compartidas:

- Respuesta: `cubic-bezier(0.2, 0, 0, 1)`.
- Transición: `cubic-bezier(0.22, 1, 0.36, 1)`.
- Secuencia científica: `linear` cuando representa tiempo.
- Sin rebotes en controles, cifras o resultados.

| Elemento | Motor | Comportamiento |
|---|---|---|
| Hover, foco, seleccionado | CSS | Color/borde, 120 ms; sin desplazar el layout |
| Entrada de sección | Motion | Opacidad y desplazamiento máximo de 8 px, 220 ms; una vez |
| Fichas relacionadas | Motion | Escalonado de 35 ms, máximo total de 140 ms |
| Navegación de página | Motion | Entrada del contenido, 170 ms; sin bloquear enlaces |
| Menú compacto | Motion | Entrada/salida de 220/170 ms; desplazamiento máximo de 12 px |
| Indicador de terminal | Motion | Una activación de 500 ms tras una acción real |
| Estado de cálculo | Motion | Cambio de estado de 120 ms; sin espera artificial |
| Esquema científico explicativo | Anime.js | Secuencia activada por el usuario, 500 ms por paso |
| Cambio de datos de gráfico | ECharts | Actualización de 220 ms; entrada inicial máxima de 500 ms |

Reglas:

- Motion controla la interfaz; Anime.js controla únicamente su escena explicativa; ECharts controla sus series.
- Ningún elemento será animado por dos motores.
- Animar wrappers de recursos originales sin deformar ni redibujar el emblema.
- No animar cifras científicas recorriendo valores intermedios.
- No añadir glitch, parpadeo continuo, partículas aleatorias ni bucles decorativos.
- Las animaciones explicativas tendrán estado final estable y repetición explícita.
- Cancelar animaciones y observadores al desmontar.
- El contenido seguirá disponible sin JavaScript.

Movimiento reducido:

- `MotionConfig reducedMotion="user"` y adaptación mediante `useReducedMotion`.
- Eliminar desplazamientos, secuencias automáticas y reproducción temporal.
- ECharts con animación deshabilitada.
- Anime.js mostrará el estado final.
- Cambios de opacidad opcionales de hasta 100 ms.
- Mantener las mismas acciones, datos y mensajes.

La [documentación de Motion](https://motion.dev/docs/react-use-reduced-motion) permite adaptar la animación a esa preferencia. El [Easing Editor de Anime.js](https://animejs.com/easing-editor) se utilizará durante desarrollo para preparar curvas; no se incluirá en el producto.

## 4. `docs/SCIENCE_DATA_SPEC.md`

### Fuentes y límites comprobados

| Sitio / carpeta | Predicciones guardadas | Restricción principal |
|---|---:|---|
| ACME / `ACME` | 52 | Validación; holdout de 50 registros únicamente agregado |
| BASS-II / `BASS-II` | 0 | Existen mediciones y métricas históricas; no pronósticos individuales exportados |
| SAFFIRE-II / `SAFFIRE` | 9 | LOOCV repetida, una misión; respuesta local de CO₂ |
| SAME-R / `SAME` | 117 | 52 filas de tamaño y 65 de detección; estas últimas son proxies |
| FLEX / `flex` | 50 | Grupo de validación `NaT`; 49 observaciones válidas por objetivo |

Todos utilizan `schema_version: 2`. Los JSON originales suman aproximadamente 2.2 MB y no deben importarse completos desde componentes cliente.

El exportador existente verifica unidades, residuos, hashes, referencias y conteos. Sus comprobaciones pasan para BASS-II, SAFFIRE, SAME y FLEX. La comprobación global se detiene por dos archivos derivados ausentes de ACME.

### Recuperación de ACME

Crear una utilidad de preparación del sitio que:

1. Lea `acme_tad_pilot.csv` conservando encabezado, campos y orden.
2. Seleccione únicamente las filas `train` y `validation`.
3. Serialice con `csv.DictWriter`, UTF-8 y saltos CRLF.
4. Compruebe los SHA-256 esperados antes de escribir.
5. Cree únicamente los dos archivos derivados ausentes.
6. Si ya existen, valide sus hashes y no los sobrescriba si difieren.

La reconstrucción en memoria ya reproduce exactamente los hashes: **134 filas de entrenamiento y 52 de validación**.

No ejecutar `prepare.py --check` como comprobación de solo lectura: actualmente regenera archivos. No entrenar, abrir nuevamente el holdout ni reescribir predicciones o registros.

### Pipeline estático

Ubicar las utilidades nuevas bajo `frontend/scripts/`, manteniendo el exportador original intacto.

Secuencia:

1. Restaurar derivados ACME si faltan.
2. Ejecutar `python3 investigations/export_predictions.py --check`.
3. Leer los cinco exports y las tablas expresamente necesarias.
4. Generar archivos web compactos.
5. Validar la salida completa antes de sustituir la generación anterior.

Contrato mínimo publicado:

- `data/v1/catalog.json`: identidad, rutas y resumen pequeño.
- `data/v1/{slug}/summary.json`: métricas, unidades, validación y límites.
- `observations.json` y `predictions.json`: registros separados.
- `series/{case}.json`: series por caso, cuando existan.
- `model.json`: únicamente para una fórmula ejecutable ya verificada.

Cada conjunto conservará:

- Archivo de origen, SHA-256 y localizador de fila o JSON Pointer.
- Identificadores originales.
- Unidad y transformación.
- Tipo de evidencia.
- Partición y contexto de validación.
- Límites y estado de disponibilidad.
- Hash del export original.

Los números conservarán su precisión; el redondeo será exclusivo de presentación. `null` seguirá significando ausencia y nunca cero. Los residuos mantendrán la definición `actual - predicted`.

La generación será determinista, sin fechas variables ni lecturas de red. Un error de hash, fuente o unidad impedirá publicar datos científicos.

### Gráficos y series

- ACME: observaciones del piloto y paridad de las 52 predicciones. No construir puntos individuales del holdout.
- SAFFIRE-II: nueve respuestas y predicciones; series de sensores cargadas por ensayo. Conservar ventanas `[-30,0)` y `[150,180)` segundos.
- BASS-II: tasas, comparaciones publicadas, métricas por modelo/horizonte y series CSV existentes de B1/M1. Diferenciar frente medido y ajuste.
- SAME-R: tamaños, respuesta por régimen y paridad separada por tarea; conservar la transformación logarítmica.
- FLEX: desenlaces, predicciones guardadas y los tres archivos originales de historia de gotas.

Las series grandes se dividirán por caso durante la generación. Para vistas generales se usarán agregaciones temporales deterministas con unidades e intervalo documentados; nunca interpolación para rellenar huecos.

ECharts utilizará módulos de líneas, barras y dispersión según necesidad, carga diferida y destrucción de instancias al desmontar. Cada gráfico tendrá título, unidades, leyenda, procedencia y tabla o resumen accesible.

### Laboratorios sin backend

Alcance confirmado: **casos guardados y cálculos verificables**.

| Laboratorio | Implementación acordada |
|---|---|
| SAFFIRE-II | Inferencia TypeScript con los dos coeficientes guardados |
| ACME | Explorar las 52 predicciones y sus condiciones; entradas nuevas no disponibles inicialmente |
| BASS-II | Seleccionar B1/M1 y métricas históricas por horizonte; no generar pronósticos individuales |
| SAME-R | Seleccionar escenarios ya guardados; sin reconstruir regresores ni interpolar resultados |
| FLEX | Seleccionar registros con predicción guardada; sin ejecutar Random Forest en el navegador |

SAFFIRE-II permite esta fórmula comprobada:

- Silicone: `-2.3719876375000006 ppm`.
- Otros materiales admitidos: `55.61162158009801 × 20 / flow_cm_s ppm`.
- Dominio de flujo observado: aproximadamente `19.9757–24.9887 cm/s`.
- Mantener separadas la inferencia del modelo completo y las predicciones LOOCV.
- No ofrecer presión u oxígeno como entradas: el modelo no ajusta esas respuestas.

SAME-R dispone de 90 escenarios guardados, con edades discretas y una bandera `extrapolated`. Los resultados extrapolados conservarán esa señal. Las probabilidades de detección no se presentarán como seguridad operativa.

En ACME y FLEX, los presets filtrarán casos existentes y mostrarán sus condiciones completas. Una combinación sin evidencia permanecerá visible como no disponible, con explicación; no se elegirá silenciosamente el caso “más cercano”.

### Conflictos con Figma y controles de integridad

El diseño manda sobre la composición; las fuentes científicas mandan sobre los valores y afirmaciones.

Ejemplo comprobado: Figma muestra `2298.37 K` para `19150N1`; la predicción guardada es `2298.9414285441826 K`. Se mostrará el valor guardado con el redondeo de presentación correspondiente.

Pruebas focalizadas:

- Reconstrucción ACME: hashes exactos y conteos.
- Generación repetida: mismos bytes.
- Unidades, transformaciones, `null`, residuos y localizadores.
- Separación de validación/holdout y de tareas SAME-R.
- Fórmula SAFFIRE: ambos grupos, extremos permitidos, cero y entradas no finitas.
- Casos inexistentes: disponibilidad explícita, sin datos inventados.

No se modificarán modelos, datasets originales, calibraciones ni historiales.

## 5. `frontend/AGENTS.md`

### Reglas para ejecución futura

- Hablar con el usuario en español; escribir código, comentarios y documentación en inglés.
- Leer las cuatro especificaciones antes de modificar su área.
- Respetar la prioridad visual y los frames asignados por tamaño.
- No reutilizar el frontend anterior ni recuperarlo del historial.
- No modificar originales científicos, modelos, calibraciones, protocolos ni ledgers.
- No entrenar modelos durante build o navegación.
- No introducir nuevas bibliotecas, APIs o abstracciones sin una necesidad concreta del plan.
- No hacer commit, push, merge, cambios remotos ni despliegue sin instrucción explícita.
- Toda discrepancia científica debe resolverse con evidencia o mostrarse como no disponible.
- No declarar una página terminada sin revisar el contenido completo, su responsive y sus interacciones.

### Responsabilidades y propiedad de archivos

| Agente | Archivos autorizados | Entrega verificable |
|---|---|---|
| Coordinador | Los cinco documentos, contratos, configuración y futuro workflow | Decisiones consistentes, integración y aceptación |
| Frontend | Rutas, UI, estilos, recursos visuales y contenido editorial bajo `frontend/` | Página funcional comparada con Figma |
| Datos | Scripts científicos nuevos, contratos bajo entities, fixtures y JSON generados | Generación determinista y procedencia comprobada |
| Tareas pequeñas | Únicamente archivos asignados expresamente | Traducción, revisión de enlaces o ajustes acotados |

Excepción limitada para el agente de datos: crear los dos CSV derivados ausentes de ACME, después de comprobar sus hashes. No queda autorizado a regenerar otros archivos de esa investigación.

Reglas de coordinación:

- Frontend controla `package.json` y el lockfile.
- Datos controla el contrato científico y su generación.
- Un solo escritor por archivo.
- Diccionarios, tipos compartidos y configuración se transfieren entre agentes de forma secuencial.
- No se crearán ramas ni worktrees durante esta planificación.
- Usar dos agentes paralelos únicamente para frontend y datos cuando existan tareas independientes suficientes.
- Las tareas pequeñas se agruparán; no crear un agente por botón, traducción o archivo.
- Una decisión arquitectónica nueva vuelve al coordinador; el agente económico no rediseña la solución.

### Criterio de cierre de tarea

Cada entrega indicará:

1. Comportamiento implementado y frames utilizados.
2. Archivos modificados.
3. Comprobaciones realizadas y su resultado.
4. Diferencias pendientes, con causa concreta.

Actualizar el estado dentro del plan maestro; no crear reportes adicionales.

### Primera tarea lista para delegar: V1 — Inicio fiel y funcional

**Objetivo:** entregar Inicio completo en EN/ES, con navegación funcional y vista local, reproduciendo `215:2`, `385:3` y `385:137`.

**Trabajo autorizado cuando comience la implementación:**

- Crear Next.js/TypeScript/FSD mínimo bajo `frontend/`.
- Configurar exportación estática y prefijo del repositorio.
- Preparar tokens, fuentes locales y SVG originales del Inicio.
- Implementar cabecera, menú, selector de idioma y pie correspondiente a cada tamaño.
- Implementar todas las secciones de Inicio según su variante.
- Incorporar únicamente las animaciones iniciales de Motion.
- Crear destinos mínimos traducidos para enlaces pendientes.
- Dejar el servidor local funcionando y comunicar su URL.

**Aceptación:** revisión a 390, 768 y 1440 px; comparación directa de la versión española con Figma; inglés completo sin recortes; teclado y menú funcionales; movimiento reducido; typecheck y exportación estática correctos. No avanzar a completar las otras páginas antes de la revisión visual de Inicio.

No se instalaron dependencias, escribieron archivos ni ejecutaron suites de pruebas.  
Riesgos pendientes: materializar los documentos y recuperar los derivados ACME antes de publicar datos.
