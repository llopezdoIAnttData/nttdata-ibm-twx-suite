# dashboard-corporate-design — Rediseño Corporativo del Tablero GenAI Efficiency Metrics

## Descripción
Skill para aplicar un rediseño corporativo completo al tablero de métricas GenAI Efficiency Metrics ubicado en:
`C:\Users\llopezdo\Downloads\DashbaordMetricas\genai-efficiency-metrics`

Aplica identidad visual NTT DATA, mejoras de UX/UI de nivel enterprise, y optimizaciones para dashboards de métricas de productividad con IA.

---

## Contexto del proyecto

**Stack:** React 18 + Vite + Tailwind CSS + Recharts + xlsx  
**Páginas:** ResumenEjecutivo, ImpactoIA, Dashboard, Detalle, Registro, Carga  
**Métricas clave:** IPI, reducción de horas, adopción IA, semáforo de actividades  
**Caso de uso:** Seguimiento de eficiencia GenAI en migración IBM BPM → Appian (Profuturo / NTT DATA México)

---

## PROMPT COMPLETO DE REDISEÑO

Cuando se invoque este skill, ejecutar el siguiente prompt de diseño completo contra el proyecto:

---

### 🎨 PROMPT: Rediseño Corporativo Enterprise — GenAI Efficiency Metrics Dashboard

Eres un experto en **UI/UX de nivel enterprise** especializado en dashboards de métricas de productividad y analítica corporativa. Tu tarea es aplicar un **rediseño corporativo completo** al proyecto React ubicado en:

```
C:\Users\llopezdo\Downloads\DashbaordMetricas\genai-efficiency-metrics
```

#### IDENTIDAD DE MARCA — NTT DATA

**Paleta primaria:**
```js
// tailwind.config.js → theme.extend.colors.ntt
{
  50:  '#e6f0ff',
  100: '#cce0ff',
  200: '#99c2ff',
  300: '#66a3ff',
  400: '#3385ff',
  500: '#0066ff',  // NTT DATA Blue principal
  600: '#0052cc',
  700: '#003d99',
  800: '#002966',
  900: '#001433',  // sidebar/headers oscuros
}
```

**Paleta de estado (semáforo):**
```js
verde:    '#059669'  // Emerald-600
amarillo: '#d97706'  // Amber-600
rojo:     '#dc2626'  // Red-600
gris:     '#94a3b8'  // Slate-400
```

**Tipografía:** Inter (ya configurada). Escala: `text-[10px]` labels, `text-xs` body, `text-sm` cards, `text-base` títulos, `text-2xl`/`text-3xl` KPI destacados.

---

#### SISTEMA DE DISEÑO A IMPLEMENTAR

##### 1. `tailwind.config.js` — Extender con tokens corporativos
```js
// Agregar a theme.extend:
colors: {
  ntt: { 50:'#e6f0ff', 100:'#cce0ff', 200:'#99c2ff', 300:'#66a3ff', 400:'#3385ff', 500:'#0066ff', 600:'#0052cc', 700:'#003d99', 800:'#002966', 900:'#001433' },
  status: { success:'#059669', warning:'#d97706', danger:'#dc2626', neutral:'#94a3b8' }
},
boxShadow: {
  'card':     '0 1px 3px rgba(0,20,51,0.06), 0 1px 2px rgba(0,20,51,0.04)',
  'card-hover':'0 4px 12px rgba(0,82,204,0.12), 0 2px 4px rgba(0,82,204,0.06)',
  'kpi':      '0 2px 8px rgba(0,82,204,0.10)',
},
borderRadius: {
  'card': '16px',
  'chip': '999px',
},
fontFamily: {
  sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
}
```

##### 2. `src/index.css` — Variables CSS globales y tokens base
```css
:root {
  --color-bg:        #f0f4f9;
  --color-surface:   #ffffff;
  --color-border:    #e8edf5;
  --color-ntt-900:   #001433;
  --color-ntt-600:   #0052cc;
  --color-ntt-500:   #0066ff;
  --sidebar-width:   256px;
  --radius-card:     16px;
  --radius-chip:     999px;
  --shadow-card:     0 1px 3px rgba(0,20,51,0.06), 0 1px 2px rgba(0,20,51,0.04);
  --transition-base: 150ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Smooth font rendering */
*, *::before, *::after { box-sizing: border-box; }
body {
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  background: var(--color-bg);
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Focus visible accesible */
:focus-visible { outline: 2px solid #0066ff; outline-offset: 2px; }

/* Scrollbar corporativo */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* Sidebar scrollbar */
.sidebar-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); }

/* KPI entrance animation */
@keyframes kpi-enter {
  from { opacity: 0; transform: translateY(8px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.kpi-value { animation: kpi-enter 0.35s cubic-bezier(0.34,1.56,0.64,1) both; }

/* Chart card hover */
.chart-card { transition: box-shadow var(--transition-base), transform var(--transition-base); }
.chart-card:hover { box-shadow: var(--shadow-card-hover); transform: translateY(-1px); }

/* Status pulse for live indicator */
@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
.status-live { animation: status-pulse 2s ease-in-out infinite; }
```

##### 3. `src/components/KpiCard.jsx` — Rediseño completo
Crear un componente con estas características:
- Borde izquierdo de 3px de color accent
- Fondo blanco con `box-shadow: var(--shadow-card)`
- Hover con elevación suave (`translateY(-2px)` + shadow mayor)
- Número KPI en `text-3xl font-black` con clase `kpi-value`
- Label en `text-[10px] font-black uppercase tracking-widest text-slate-400`
- Sub-texto en `text-[11px] text-slate-400`
- Trend badge: pill con fondo semitransparente del color accent, flecha ↑↓
- Accents disponibles: `blue` (#0066ff), `cyan` (#0891b2), `violet` (#7c3aed), `green` (#059669), `amber` (#d97706), `red` (#dc2626)
- Icon en esquina superior derecha en círculo con fondo accent/10

```jsx
// Estructura visual esperada:
// ┌─────────────────────────────────────┐
// │ ▌  LABEL UPPERCASE              🎯 │  ← accent border left + icon circle
// │    3,247 h                          │  ← valor grande
// │    Sub texto · trend badge ↑        │  ← metadata
// └─────────────────────────────────────┘
```

##### 4. `src/components/Sidebar.jsx` — Sidebar enterprise
- Fondo: `#001433` (ntt-900)
- Logo NTT DATA: badge blanco con texto azul oscuro, tipografía `font-black text-[11px]`
- Separador con gradiente sutil `border-white/10`
- Nav items activos: fondo blanco, texto ntt-900, sombra `shadow-lg`
- Nav items inactivos: texto `white/65`, hover `white/90` + fondo `white/8`
- Iconos SVG heroicons outline (20px)
- Footer con indicador "En línea" pulsante verde + fecha actual
- Badge de versión en `white/20`
- Sección de proyecto con `text-white/40` para el subtítulo
- Colapso responsive en mobile (hamburger menu con drawer)

##### 5. `src/components/PageHeader.jsx` — Header de página
```jsx
// Layout:
// ┌──────────────────────────────────────────────────────────┐
// │  EYEBROW (uppercase, ntt-500, tracking-wide)             │
// │  Título principal (text-2xl font-black text-slate-900)   │
// │  Descripción (text-sm text-slate-500)              [CTA] │
// └──────────────────────────────────────────────────────────┘
```
- Eyebrow: `text-[10px] font-black uppercase tracking-[0.2em] text-ntt-600`
- Título: `text-[22px] font-black text-slate-900 leading-tight`
- Descripción: `text-[13px] text-slate-500`
- Línea separadora inferior: `border-b border-slate-200/60 pb-4`
- Slot `actions` con chips/badges a la derecha
- Status chip corporativo: pill con punto pulsante y color semafórico

##### 6. `src/pages/Dashboard.jsx` — Mejoras UX
- **Barra de filtros mejorada:** chips tipo pill seleccionables (no dropdowns estándar) con estado visual activo (relleno ntt-600 + texto blanco)
- **Banner ejecutivo:** gradiente diagonal `from-ntt-900 via-ntt-800 to-ntt-700` con ruido de textura sutil (`bg-noise`)
- **Grid KPIs:** layout `grid-cols-2 sm:grid-cols-3 xl:grid-cols-6` con gap-3
- **ChartCard mejorado:** header con título + subtítulo + badge de estado + botón de expand opcional
- **Gráfica IPI:** barras con gradiente (verde ≥1.0, rojo <1.0), tooltip corporativo, referencia line con label integrado
- **Donut semáforo:** `innerRadius=65 outerRadius=88`, texto central con total de actividades, leyenda debajo con conteos
- **Empty state:** componente unificado cuando no hay datos filtrados (ilustración SVG + CTA)
- **Responsive:** stack vertical en mobile, 2 cols en tablet, full grid en desktop

##### 7. `src/pages/ResumenEjecutivo.jsx` — Mejoras UX
- **MigrationDial:** agregar anillo de track con gradiente, texto secundario "de N actividades", sombra interna
- **Proyección IA:** card oscura con dos métricas grandes + badge de ahorro en semanas con animación countup
- **Fases:** progress bars con gradiente de izquierda a derecha, transición animada al cargar, indicador de horas ahorradas en badge verde
- **Items críticos:** tabla con avatar de equipo (inicial del nombre), badge semáforo, brecha en porcentaje rojo, ordenable por brecha
- **Semáforo grid:** 4 cards con bordes de color, número grande animado, descripción del criterio

##### 8. `src/pages/ImpactoIA.jsx` — Visualizaciones de impacto
Asegurarse de que incluya:
- **ROI Card:** cálculo de horas ahorradas × costo hora promedio (configurable), mostrado como ahorro económico estimado en banner destacado
- **Adopción por equipo:** gráfica radar o heatmap de adopción × efectividad
- **Tendencia semanal:** área chart con dos series (ahorro acumulado vs meta) con línea de objetivo punteada
- **Comparativa herramientas:** horizontal bar chart ordenado por efectividad, con badges de % efectividad

##### 9. Componentes de utilidad a crear/mejorar

**`src/components/SemaforoBadge.jsx`:**
```jsx
// Badge compacto con color, punto y texto
// Tamaños: sm (10px), md (11px default), lg (12px)
// Formas: pill (default), square
```

**`src/components/ChartCard.jsx`** (extraer del Dashboard):
```jsx
// Props: title, subtitle, badge, actions, height, loading, empty
// Estado loading: skeleton shimmer animation
// Estado empty: slot para empty state component
```

**`src/components/EmptyState.jsx`:**
```jsx
// Props: icon, title, description, action
// Fondo: bg-slate-50 rounded-2xl, icono grande centrado
```

**`src/components/FilterBar.jsx`** (extraer de Dashboard):
```jsx
// Filtros como pill buttons seleccionables
// Botón "Limpiar filtros" solo visible si hay filtros activos
// Conteo de resultados integrado
```

**`src/components/StatRow.jsx`:**
```jsx
// Fila de stat: label izquierda + valor derecha
// Opcional: mini progress bar debajo
// Opcional: delta vs período anterior
```

---

#### PRINCIPIOS DE UX PARA MÉTRICAS

1. **Data-ink ratio:** Eliminar bordes, líneas de grid y decoración innecesaria. Solo mostrar lo que ayuda a leer el dato.

2. **Jerarquía visual clara:**
   - Nivel 1 (KPI principal): `text-3xl font-black` + color accent
   - Nivel 2 (subtítulo KPI): `text-sm font-semibold text-slate-600`
   - Nivel 3 (metadata): `text-xs text-slate-400`

3. **Semáforo consistente:** Usar SIEMPRE los mismos colores para verde/amarillo/rojo en toda la app. Nunca usar rojo para texto normal.

4. **Tooltips informativos:** Todos los gráficos deben tener tooltips con:
   - Título del punto de datos
   - Valor numérico con unidad
   - Delta vs objetivo (si aplica)
   - Formato: fondo blanco, borde `border-slate-200`, sombra `shadow-xl`, `rounded-xl`

5. **Estado de carga:** Skeleton loaders (shimmer) para cada sección. Nunca spinner global.

6. **Feedback inmediato:** Filtros deben actualizar gráficas instantáneamente. Usar `useMemo` agresivamente.

7. **Accesibilidad:**
   - Colores de semáforo con ícono adicional (no solo color)
   - `aria-label` en todos los botones de icono
   - Contraste mínimo WCAG AA en todos los textos
   - `focus-visible` con anillo azul ntt-500

8. **Mobile-first responsive:**
   - Sidebar: drawer en mobile (< 768px)
   - KPI cards: 2 columnas en mobile
   - Gráficas: altura reducida en mobile (h-48 vs h-64)
   - Tabla detalle: scroll horizontal en mobile

9. **Micro-interacciones:**
   - Cards con hover elevation (translateY + shadow)
   - Botones con ripple effect en hover
   - Números KPI con animación countUp al montar
   - Progress bars con transición de 700ms al cargar

10. **Print / Export CSS:**
    ```css
    @media print {
      .sidebar, .filter-bar, .actions { display: none; }
      .chart-card { break-inside: avoid; }
      body { background: white; }
    }
    ```

---

#### CHECKLIST DE IMPLEMENTACIÓN

Al finalizar el rediseño, verificar que:

- [ ] `tailwind.config.js` tiene los tokens NTT DATA completos
- [ ] `index.css` tiene todas las variables CSS y animaciones
- [ ] `KpiCard.jsx` usa accent border + hover elevation + animación
- [ ] `Sidebar.jsx` tiene nav activo con fondo blanco y responsive mobile
- [ ] `PageHeader.jsx` usa eyebrow + título + descripción + slot actions
- [ ] `Dashboard.jsx` usa FilterBar con pills, no dropdowns nativos
- [ ] `ResumenEjecutivo.jsx` tiene MigrationDial animado + fases con progress
- [ ] `ImpactoIA.jsx` tiene ROI card + tendencia semanal + adopción por equipo
- [ ] Todos los gráficos tienen CustomTooltip corporativo
- [ ] EmptyState funciona en todas las vistas con datos vacíos
- [ ] App es responsive en 375px, 768px, 1280px, 1440px
- [ ] `npm run build` pasa sin errores ni warnings

---

#### COMANDO PARA INICIAR

```bash
cd "C:\Users\llopezdo\Downloads\DashbaordMetricas\genai-efficiency-metrics"
npm run dev
```

Verificar en `http://localhost:5173` después de cada cambio importante.
