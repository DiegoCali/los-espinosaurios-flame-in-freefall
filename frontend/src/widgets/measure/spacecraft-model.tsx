// Stylised uncrewed cargo spacecraft for the SAFFIRE-II cinematic (conceptual, not to scale).
// Drawn in local coordinates: cargo module centred near (-45, 0), service module to the right,
// two circular fan-type solar arrays on booms. Gores carry data-i so the parent can deploy them.

export const CRAFT_CARGO_CENTER_X = -45;
const GORES = 10, R = 62, GORE_DEG = 360 / GORES;
const wedge = (r: number) => { const a = (GORE_DEG * Math.PI) / 180; return `M0 0 L${r} 0 A${r} ${r} 0 0 1 ${(r * Math.cos(a)).toFixed(2)} ${(r * Math.sin(a)).toFixed(2)} Z`; };

export function CraftDefs() {
  return <>
    <linearGradient id="crHull" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#5f6b78" /><stop offset="10%" stopColor="#dfe5ea" /><stop offset="26%" stopColor="#ffffff" /><stop offset="48%" stopColor="#c8d0d8" /><stop offset="78%" stopColor="#7d8894" /><stop offset="100%" stopColor="#2d3742" />
    </linearGradient>
    <linearGradient id="crService" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#3a4552" /><stop offset="22%" stopColor="#a7b2bd" /><stop offset="50%" stopColor="#6f7b87" /><stop offset="100%" stopColor="#1f2832" />
    </linearGradient>
    <linearGradient id="crGold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#6b4f1d" /><stop offset="25%" stopColor="#f3d48a" /><stop offset="55%" stopColor="#c9a24f" /><stop offset="100%" stopColor="#4a3612" />
    </linearGradient>
    <linearGradient id="crRing" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#2d3742" /><stop offset="50%" stopColor="#b8c2cc" /><stop offset="100%" stopColor="#3a4552" /></linearGradient>
    <linearGradient id="crBell" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#3a4552" /><stop offset="100%" stopColor="#11171e" /></linearGradient>
    <radialGradient id="crGlint" cx="30%" cy="25%" r="60%"><stop offset="0%" stopColor="#ffffff" stopOpacity=".55" /><stop offset="100%" stopColor="#ffffff" stopOpacity="0" /></radialGradient>
    <radialGradient id="crGoreShade" cx="0%" cy="0%" r="100%"><stop offset="0%" stopColor="#000" stopOpacity=".35" /><stop offset="60%" stopColor="#000" stopOpacity="0" /><stop offset="100%" stopColor="#77c3ed" stopOpacity=".18" /></radialGradient>
    <pattern id="crCells" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#0f3561" /><path d="M7 0H0V7" stroke="#2f6fb2" strokeWidth=".7" fill="none" /><rect x="1" y="1" width="2.4" height="2.4" fill="#1d4f86" /></pattern>
    <filter id="crSoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" /></filter>
  </>;
}

function SolarArray({ side }: { side: 1 | -1 }) {
  return <g transform={`translate(66 ${side * 132})`}>
    <g className="cr-array" data-side={side}>
      {Array.from({ length: GORES }, (_, i) => <g key={i} className="cr-gore" data-i={i}>
        <path d={wedge(R)} fill="url(#crCells)" stroke="#d6b25e" strokeWidth=".9" />
        <path d={wedge(R)} fill="url(#crGoreShade)" />
        <line x1="0" y1="0" x2={R} y2="0" stroke="#e8c97a" strokeWidth="1.2" />
      </g>)}
      <circle className="cr-array-glint" r={R} fill="url(#crGlint)" opacity="0" />
    </g>
    <circle r="8" fill="#8c9eae" stroke="#2d3742" /><circle r="3" fill="#2d3742" />
  </g>;
}

export function CargoCraft({ labels }: { labels: { cargo: string; service: string; arrays: string } }) {
  return <g className="cr-body">
    {/* Booms */}
    {[-1, 1].map(s => <path key={s} d={`M60 ${s * 30} L66 ${s * 70}`} stroke="#9aa6b2" strokeWidth="3.5" strokeLinecap="round" />)}
    <SolarArray side={-1} /><SolarArray side={1} />

    {/* Service module: chamfered body, gold insulation band, thrusters and engine bell */}
    <path d="M34 -36 L92 -36 L102 -26 L102 26 L92 36 L34 36 Z" fill="url(#crService)" stroke="#1f2832" />
    <rect x="46" y="-36" width="34" height="72" fill="url(#crGold)" opacity=".92" />
    {[52, 60, 68, 76].map(x => <line key={x} x1={x} x2={x} y1="-36" y2="36" stroke="#6b4f1d" strokeOpacity=".45" />)}
    <path d="M102 -14 L120 -22 L120 22 L102 14 Z" fill="url(#crBell)" stroke="#0b1119" />
    <ellipse cx="120" cy="0" rx="3.5" ry="22" fill="#05080d" stroke="#3a4552" />
    {[[-1, 40], [1, 40], [-1, 90], [1, 90]].map(([s, x], i) => <g key={i} transform={`translate(${x} ${s * 37})`}><rect x="-5" y={s > 0 ? 0 : -6} width="10" height="6" fill="#3a4552" /><path d={`M-2 ${s * 6} L-3.5 ${s * 11} L3.5 ${s * 11} L2 ${s * 6} Z`} fill="#11171e" /><circle className="cr-puff" cx="0" cy={s * 16} r="4" fill="#d9f1ff" opacity="0" /></g>)}
    <g transform="translate(72 -36)"><line x1="0" y1="0" x2="0" y2="-16" stroke="#9aa6b2" strokeWidth="2" /><path d="M-11 -16 Q0 -30 11 -16 Z" fill="#dfe5ea" stroke="#5f6b78" /><circle cx="0" cy="-19" r="1.6" fill="#5f6b78" /></g>
    <line x1="92" y1="36" x2="98" y2="58" stroke="#9aa6b2" strokeWidth="1.2" />

    {/* Interface ring */}
    <rect x="28" y="-41" width="8" height="82" rx="2" fill="url(#crRing)" stroke="#1f2832" />

    {/* Cargo module: cylinder with seams, stringers and insulation patches */}
    <rect x="-128" y="-40" width="158" height="80" rx="18" fill="url(#crHull)" stroke="#2d3742" strokeWidth="1.2" />
    {[-106, -84, -62, -40, -18, 4].map(x => <line key={x} x1={x} x2={x} y1="-39" y2="39" stroke="#2d3742" strokeOpacity=".22" />)}
    <line x1="-124" x2="26" y1="0" y2="0" stroke="#2d3742" strokeOpacity=".12" />
    <rect x="-96" y="-40" width="26" height="80" fill="#d9c58f" opacity=".22" />
    <rect x="-30" y="-40" width="18" height="80" fill="#d9c58f" opacity=".16" />
    {[-118, -52, 14].map(x => <rect key={x} x={x} y="-44" width="6" height="5" rx="1" fill="#8c9eae" />)}
    <rect x="-70" y="-46" width="20" height="7" rx="1.5" fill="#5f6b78" /><rect x="-66" y="-50" width="12" height="4" fill="#8c9eae" />

    {/* Berthing ring and hatch at the front */}
    <ellipse cx="-128" cy="0" rx="9" ry="31" fill="url(#crRing)" stroke="#1f2832" />
    <ellipse cx="-131" cy="0" rx="5" ry="22" fill="#11171e" stroke="#5f6b78" />
    {[-1, 1].map(s => <rect key={s} x="-136" y={s * 26 - 3} width="6" height="6" fill="#9aa6b2" />)}

    {/* Lighting: sun glint on top, earthshine along the bottom */}
    <ellipse className="cr-glint" cx="-60" cy="-24" rx="58" ry="7" fill="#ffffff" opacity=".5" filter="url(#crSoft)" />
    <path d="M-120 38 Q-50 46 26 38" stroke="#77c3ed" strokeWidth="3" strokeOpacity=".55" fill="none" filter="url(#crSoft)" />

    {/* Navigation lights */}
    <circle className="cr-nav cr-nav-red" cx="-110" cy="-41" r="2.6" fill="#ff3b4e" />
    <circle className="cr-nav cr-nav-green" cx="-110" cy="41" r="2.6" fill="#3dff9a" />
    <circle className="cr-strobe" cx="-138" cy="0" r="2.2" fill="#ffffff" />

    {/* Callouts (shown in orbit, hidden before the zoom) */}
    <g className="cr-callouts">
      <g className="cr-callout"><path d="M-80 -42 L-104 -96 L-190 -96" /><circle cx="-80" cy="-42" r="2.5" /><text x="-190" y="-102">{labels.cargo}</text></g>
      <g className="cr-callout"><path d="M100 30 L150 92 L250 92" /><circle cx="100" cy="30" r="2.5" /><text x="250" y="86" textAnchor="end">{labels.service}</text></g>
      <g className="cr-callout"><path d="M112 -150 L170 -196 L262 -196" /><circle cx="112" cy="-150" r="2.5" /><text x="262" y="-202" textAnchor="end">{labels.arrays}</text></g>
    </g>
  </g>;
}
