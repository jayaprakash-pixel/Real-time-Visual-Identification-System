# Architecture â€” Real-time Visual Identification System

Each box's id is `comp-<key>`, matching the `component` column in `tasks.json` exactly (lowercase letters only). The cockpit recolours boxes from live task state: grey = untouched, amber = in progress, green = done and verified.

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 470" font-family="system-ui, sans-serif" font-size="14" role="img" aria-label="Real-time Visual Identification System architecture">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#8a8a85"/>
    </marker>
  </defs>

  <text x="20" y="40" font-size="12" opacity="0.7">INPUT</text>
  <text x="20" y="180" font-size="12" opacity="0.7">SERVER (port 8010)</text>
  <text x="20" y="340" font-size="12" opacity="0.7">OPERATOR</text>

  <rect id="comp-supabase" x="140" y="20" width="200" height="70" rx="10"/>
  <text x="240" y="50" text-anchor="middle" font-weight="600">Supabase</text>
  <text x="240" y="72" text-anchor="middle" font-size="12">persons table Â· photo bucket</text>

  <rect id="comp-camera" x="620" y="20" width="200" height="70" rx="10"/>
  <text x="720" y="50" text-anchor="middle" font-weight="600">Camera</text>
  <text x="720" y="72" text-anchor="middle" font-size="12">phone MJPEG Â· CCTV Â· file</text>

  <rect id="comp-bridge" x="140" y="160" width="200" height="80" rx="10"/>
  <text x="240" y="192" text-anchor="middle" font-weight="600">Integration bridge</text>
  <text x="240" y="214" text-anchor="middle" font-size="12">person sync Â· on_match</text>

  <rect id="comp-vision" x="380" y="160" width="200" height="80" rx="10"/>
  <text x="480" y="192" text-anchor="middle" font-weight="600">AI vision (Module 2)</text>
  <text x="480" y="214" text-anchor="middle" font-size="12">YuNet Â· SFace Â· verify</text>

  <rect id="comp-alerts" x="620" y="160" width="200" height="80" rx="10"/>
  <text x="720" y="192" text-anchor="middle" font-weight="600">Alert engine (Module 3)</text>
  <text x="720" y="214" text-anchor="middle" font-size="12">gate Â· store Â· dispatch</text>

  <rect id="comp-server" x="380" y="290" width="440" height="50" rx="10"/>
  <text x="600" y="320" text-anchor="middle" font-weight="600">FastAPI: auth Â· detections Â· persons Â· MJPEG Â· WebSocket</text>

  <rect id="comp-frontend" x="380" y="380" width="260" height="70" rx="10"/>
  <text x="510" y="410" text-anchor="middle" font-weight="600">Frontend (Module 1)</text>
  <text x="510" y="432" text-anchor="middle" font-size="12">React Â· popup Â· alarm</text>

  <rect id="comp-proof" x="680" y="380" width="140" height="70" rx="10"/>
  <text x="750" y="410" text-anchor="middle" font-weight="600">Proof</text>
  <text x="750" y="432" text-anchor="middle" font-size="12">end to end Â· faults</text>

  <rect id="comp-ops" x="140" y="380" width="200" height="70" rx="10"/>
  <text x="240" y="410" text-anchor="middle" font-weight="600">Ops</text>
  <text x="240" y="432" text-anchor="middle" font-size="12">phasedoc Â· PM2 Â· docs</text>

  <line x1="240" y1="90" x2="240" y2="156" stroke="#8a8a85" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="340" y1="200" x2="376" y2="200" stroke="#8a8a85" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="720" y1="90" x2="520" y2="156" stroke="#8a8a85" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="580" y1="200" x2="616" y2="200" stroke="#8a8a85" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="720" y1="240" x2="640" y2="286" stroke="#8a8a85" stroke-width="2" marker-end="url(#arrow)"/>
  <line x1="510" y1="340" x2="510" y2="376" stroke="#8a8a85" stroke-width="2" marker-end="url(#arrow)"/>
</svg>

**Flow.** The operator registers a person in the frontend. The photo lands in Supabase. The integration bridge copies new persons into the AI's reference store. The camera feeds the AI. When the AI confirms a match, the bridge passes the result to the alert engine, which checks it, stores it and tells every channel. The server exposes the stored events, the live video and a live alert channel. The frontend shows the video, plays the alarm and lists the history.
