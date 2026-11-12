#!/usr/bin/env python3
"""
Servidor Web Local para Rastreo de Páginas Web.
Proporciona una interfaz gráfica moderna en el navegador sin dependencias externas.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import webbrowser
import threading

# Importar el motor de rastreo
from tracer_core import trace_website, DEFAULT_OUTPUT_DIR

PORT = 8888

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rastreador y Verificador de Páginas Web</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f2937;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #06b6d4;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      border-bottom: 1px solid var(--card-border);
      padding: 1.25rem 2rem;
      background: rgba(17, 24, 39, 0.7);
      backdrop-filter: blur(12px);
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-weight: 700;
      font-size: 1.25rem;
      background: linear-gradient(135deg, #60a5fa, #38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .folder-badge {
      font-size: 0.8rem;
      background: #1f2937;
      color: #93c5fd;
      padding: 0.4rem 0.8rem;
      border-radius: 9999px;
      border: 1px solid #374151;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    main {
      flex: 1;
      max-width: 1100px;
      width: 100%;
      margin: 0 auto;
      padding: 2.5rem 1.5rem;
    }
    .hero {
      text-align: center;
      margin-bottom: 2.5rem;
    }
    .hero h1 {
      font-size: 2.5rem;
      font-weight: 800;
      margin-bottom: 0.75rem;
      letter-spacing: -0.025em;
    }
    .hero p {
      color: var(--text-muted);
      font-size: 1.1rem;
      max-width: 600px;
      margin: 0 auto;
    }
    .search-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 0.5rem;
      display: flex;
      gap: 0.5rem;
      max-width: 760px;
      margin: 0 auto 3rem auto;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.15);
      transition: all 0.2s;
    }
    .search-box:focus-within {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
    }
    .search-input {
      flex: 1;
      background: transparent;
      border: none;
      padding: 0.9rem 1.25rem;
      font-size: 1.1rem;
      color: var(--text);
      outline: none;
      font-family: 'JetBrains Mono', monospace;
    }
    .search-input::placeholder {
      color: #4b5563;
      font-family: 'Inter', sans-serif;
    }
    .btn-trace {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      color: white;
      border: none;
      padding: 0 1.75rem;
      border-radius: 0.75rem;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }
    .btn-trace:hover {
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      transform: translateY(-1px);
    }
    .btn-trace:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
    .quick-examples {
      display: flex;
      justify-content: center;
      gap: 0.5rem;
      margin-top: -2rem;
      margin-bottom: 2.5rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .quick-pill {
      background: #1f2937;
      color: #93c5fd;
      padding: 0.2rem 0.6rem;
      border-radius: 0.4rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    .quick-pill:hover {
      background: #374151;
    }
    .loader {
      display: none;
      text-align: center;
      padding: 3rem 0;
    }
    .spinner {
      width: 50px;
      height: 50px;
      border: 4px solid #1f2937;
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 1.25rem auto;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .results-container {
      display: none;
      animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    .saved-alert {
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      padding: 1rem 1.25rem;
      border-radius: 0.75rem;
      margin-bottom: 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }
    .saved-path {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      color: #a7f3d0;
      word-break: break-all;
    }

    .grid-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.5rem;
      position: relative;
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.25rem;
    }
    .card-title {
      font-size: 1.05rem;
      font-weight: 600;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .data-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 0.6rem 0;
      border-bottom: 1px solid rgba(31, 41, 55, 0.6);
      font-size: 0.95rem;
    }
    .data-row:last-child { border-bottom: none; }
    .data-label { color: var(--text-muted); }
    .data-val {
      font-weight: 500;
      text-align: right;
      color: #f3f4f6;
      max-width: 65%;
      word-break: break-word;
    }
    .mono { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }

    .risk-badge {
      display: inline-block;
      padding: 0.35rem 0.75rem;
      border-radius: 0.5rem;
      font-weight: 700;
      font-size: 0.85rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .risk-green { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .risk-yellow { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .risk-red { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }

    .factor-list {
      list-style: none;
      margin-top: 0.75rem;
    }
    .factor-item {
      padding: 0.45rem 0;
      font-size: 0.9rem;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      line-height: 1.4;
    }
    .history-section {
      margin-top: 3.5rem;
      border-top: 1px solid var(--card-border);
      padding-top: 2rem;
    }
    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    .history-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }
    .history-item {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 1rem;
      border-radius: 0.75rem;
      text-decoration: none;
      color: inherit;
      display: block;
      transition: all 0.2s;
    }
    .history-item:hover {
      border-color: var(--primary);
      transform: translateY(-2px);
    }
    .history-name {
      font-weight: 600;
      font-size: 0.95rem;
      margin-bottom: 0.25rem;
      color: #93c5fd;
    }
    .history-date {
      font-size: 0.8rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="m16 12-4-4-4 4M12 16V8"/></svg>
      <span>Rastreador de Páginas Web</span>
    </div>
    <div class="folder-badge">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
      <span>Carpeta: <strong>Rastreo de paginas web</strong></span>
    </div>
  </header>

  <main>
    <div class="hero">
      <h1>Rastreo e Inspección de Sitios Web</h1>
      <p>Descubre al instante de dónde proviene cualquier página, quién es su propietario, qué servidores utiliza y si es segura para ingresar.</p>
    </div>

    <form id="traceForm" class="search-box">
      <input type="text" id="targetInput" class="search-input" placeholder="Ingresa la URL o dominio (ej: 1win.lat o https://...)" required autocomplete="off">
      <button type="submit" id="btnSubmit" class="btn-trace">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <span>Rastrear</span>
      </button>
    </form>

    <div class="quick-examples">
      <span>Prueba rápida:</span>
      <span class="quick-pill" onclick="setDomain('1win.lat')">1win.lat</span>
      <span class="quick-pill" onclick="setDomain('google.com')">google.com</span>
      <span class="quick-pill" onclick="setDomain('github.com')">github.com</span>
    </div>

    <div id="loader" class="loader">
      <div class="spinner"></div>
      <p style="font-weight: 600; font-size: 1.1rem;">Rastreando infraestructura, DNS y certificados...</p>
      <p style="color: var(--text-muted); font-size: 0.9rem;">Consultando geolocalización, ASN y registros de seguridad...</p>
    </div>

    <div id="results" class="results-container">
      <div class="saved-alert">
        <div>
          <strong>✅ Reporte generado y archivado automáticamente</strong>
          <div class="saved-path" id="savedMdPath"></div>
        </div>
      </div>

      <div class="grid-cards">
        <!-- Tarjeta de Diagnóstico y Riesgo -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">🛡️ Evaluación de Seguridad</span>
            <span id="riskBadge" class="risk-badge">BAJO</span>
          </div>
          <div class="data-row">
            <span class="data-label">Puntaje de Confianza</span>
            <span class="data-val mono" id="scoreVal">85 / 100</span>
          </div>
          <div class="data-row">
            <span class="data-label">Veredicto General</span>
            <span class="data-val" id="verdictVal" style="font-size: 0.9rem;"></span>
          </div>
          <div style="margin-top: 1rem;">
            <strong style="font-size: 0.85rem; color: #9ca3af; text-transform: uppercase;">Detalles de Análisis:</strong>
            <ul id="factorsList" class="factor-list"></ul>
          </div>
        </div>

        <!-- Tarjeta de Origen y Geolocalización -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">🌍 Origen y Red (Hosting)</span>
          </div>
          <div class="data-row">
            <span class="data-label">País de Origen</span>
            <span class="data-val" id="countryVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Ciudad / Región</span>
            <span class="data-val" id="cityVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Organización / Entidad</span>
            <span class="data-val" id="orgVal" style="color: #60a5fa; font-weight: 600;">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Proveedor (ISP)</span>
            <span class="data-val" id="ispVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Sistema Autónomo (ASN)</span>
            <span class="data-val mono" id="asnVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Dirección IP Principal</span>
            <span class="data-val mono" id="ipVal">-</span>
          </div>
        </div>

        <!-- Tarjeta SSL -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">🔒 Certificado SSL / TLS</span>
            <span id="sslStatus" class="risk-badge risk-green">ACTIVO</span>
          </div>
          <div class="data-row">
            <span class="data-label">Entidad Emisora</span>
            <span class="data-val" id="sslIssuer">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Titular / Dominio</span>
            <span class="data-val mono" id="sslSubject">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Fecha de Caducidad</span>
            <span class="data-val mono" id="sslExpiry">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Días Restantes</span>
            <span class="data-val" id="sslDays">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Dominios Amparados (SAN)</span>
            <span class="data-val mono" id="sslSans" style="font-size: 0.8rem;">-</span>
          </div>
        </div>

        <!-- Tarjeta Servidor y Cabeceras -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">⚙️ Infraestructura y Servidor</span>
          </div>
          <div class="data-row">
            <span class="data-label">Servidor Web</span>
            <span class="data-val mono" id="serverVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Red de Protección (CDN)</span>
            <span class="data-val" id="cdnVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Proxy / Vía</span>
            <span class="data-val mono" id="viaVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">HSTS (Conexión Estricta)</span>
            <span class="data-val" id="hstsVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Anti-Clickjacking</span>
            <span class="data-val" id="clickjackVal">-</span>
          </div>
          <div class="data-row">
            <span class="data-label">Content-Security-Policy</span>
            <span class="data-val" id="cspVal">-</span>
          </div>
        </div>
      </div>
    </div>

    <section class="history-section">
      <div class="history-header">
        <h2 style="font-size: 1.25rem; font-weight: 700;">📂 Historial de Reportes Guardados</h2>
        <button onclick="loadHistory()" style="background: none; border: 1px solid var(--card-border); color: var(--text-muted); padding: 0.4rem 0.8rem; border-radius: 0.5rem; cursor: pointer; font-size: 0.85rem;">🔄 Actualizar</button>
      </div>
      <div id="historyList" class="history-list">
        <p style="color: var(--text-muted);">Cargando historial...</p>
      </div>
    </section>
  </main>

  <script>
    function setDomain(dom) {
      document.getElementById('targetInput').value = dom;
      document.getElementById('traceForm').dispatchEvent(new Event('submit'));
    }

    document.getElementById('traceForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const target = document.getElementById('targetInput').value.trim();
      if (!target) return;

      const btn = document.getElementById('btnSubmit');
      const loader = document.getElementById('loader');
      const results = document.getElementById('results');

      btn.disabled = true;
      loader.style.display = 'block';
      results.style.display = 'none';

      try {
        const resp = await fetch('/api/trace', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ target })
        });
        const data = await resp.json();

        if (data.error) {
          alert('Error al rastrear: ' + data.error);
          return;
        }

        renderResults(data);
        loadHistory();
      } catch (err) {
        alert('Error de conexión con el servidor de rastreo: ' + err.message);
      } finally {
        btn.disabled = false;
        loader.style.display = 'none';
      }
    });

    function renderResults(data) {
      const results = document.getElementById('results');
      const geo = data.geolocalizacion || {};
      const ssl = data.ssl || {};
      const http = data.http || {};
      const seg = data.seguridad || {};

      document.getElementById('savedMdPath').textContent = data.archivos_guardados.markdown;

      // Riesgo
      const riskBadge = document.getElementById('riskBadge');
      riskBadge.textContent = seg.nivel_riesgo;
      riskBadge.className = 'risk-badge ' + (seg.color === 'green' ? 'risk-green' : seg.color === 'yellow' ? 'risk-yellow' : 'risk-red');
      document.getElementById('scoreVal').textContent = seg.puntuacion + ' / 100';
      document.getElementById('verdictVal').textContent = seg.resumen;

      // Factores
      const factorsList = document.getElementById('factorsList');
      factorsList.innerHTML = '';
      (seg.puntos_favorables || []).forEach(p => {
        factorsList.innerHTML += `<li class="factor-item" style="color: #34d399;">✔️ ${p}</li>`;
      });
      (seg.alertas_riesgo || []).forEach(a => {
        factorsList.innerHTML += `<li class="factor-item" style="color: #f87171;">⚠️ ${a}</li>`;
      });

      // Geo
      document.getElementById('countryVal').textContent = (geo.pais || 'Desconocido') + (geo.codigo_pais ? ` (${geo.codigo_pais})` : '');
      document.getElementById('cityVal').textContent = (geo.ciudad || '-') + (geo.region ? `, ${geo.region}` : '');
      document.getElementById('orgVal').textContent = geo.organizacion || 'No identificada';
      document.getElementById('ispVal').textContent = geo.isp || '-';
      document.getElementById('asnVal').textContent = geo.asn || '-';
      document.getElementById('ipVal').textContent = data.ip_principal || '-';

      // SSL
      const sslStatus = document.getElementById('sslStatus');
      if (ssl.disponible && !ssl.expirado) {
        sslStatus.textContent = 'ACTIVO';
        sslStatus.className = 'risk-badge risk-green';
      } else {
        sslStatus.textContent = ssl.expirado ? 'EXPIRADO' : 'NO DISPONIBLE';
        sslStatus.className = 'risk-badge risk-red';
      }
      document.getElementById('sslIssuer').textContent = ssl.emisor_org || ssl.emisor || 'Desconocido';
      document.getElementById('sslSubject').textContent = ssl.sujeto || '-';
      document.getElementById('sslExpiry').textContent = ssl.valido_hasta || '-';
      document.getElementById('sslDays').textContent = (ssl.dias_restantes !== null && ssl.dias_restantes !== undefined) ? `${ssl.dias_restantes} días` : '-';
      document.getElementById('sslSans').textContent = (ssl.dominios_san || []).slice(0, 4).join(', ') || '-';

      // Servidor / HTTP
      document.getElementById('serverVal').textContent = http.servidor || 'Oculto';
      document.getElementById('cdnVal').textContent = http.cdn || 'No detectado';
      document.getElementById('viaVal').textContent = http.via || 'Ninguno';
      const secH = http.seguridad_cabeceras || {};
      document.getElementById('hstsVal').innerHTML = secH.hsts ? '<span style="color:#34d399">✅ Presente</span>' : '<span style="color:#9ca3af">❌ Ausente</span>';
      document.getElementById('clickjackVal').innerHTML = secH.x_frame_options ? '<span style="color:#34d399">✅ Presente</span>' : '<span style="color:#9ca3af">❌ Ausente</span>';
      document.getElementById('cspVal').innerHTML = secH.csp ? '<span style="color:#34d399">✅ Presente</span>' : '<span style="color:#9ca3af">❌ Ausente</span>';

      results.style.display = 'block';
      results.scrollIntoView({ behavior: 'smooth' });
    }

    async function loadHistory() {
      const container = document.getElementById('historyList');
      try {
        const resp = await fetch('/api/history');
        const list = await resp.json();
        if (list.length === 0) {
          container.innerHTML = '<p style="color: var(--text-muted);">Aún no hay reportes en la carpeta personal.</p>';
          return;
        }
        container.innerHTML = list.map(item => `
          <div class="history-item">
            <div class="history-name">${item.nombre}</div>
            <div class="history-date">📅 ${item.fecha} • 📄 ${item.tamano}</div>
          </div>
        `).join('');
      } catch (e) {
        container.innerHTML = '<p style="color: var(--danger);">Error al cargar historial.</p>';
      }
    }

    loadHistory();
  </script>
</body>
</html>
"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/history":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            
            history = []
            if DEFAULT_OUTPUT_DIR.exists():
                for f in sorted(DEFAULT_OUTPUT_DIR.glob("*.md"), key=os.path.getmtime, reverse=True):
                    stat = f.stat()
                    from datetime import datetime
                    dt = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    size_kb = f"{max(1, round(stat.st_size / 1024))} KB"
                    history.append({
                        "nombre": f.name,
                        "fecha": dt,
                        "tamano": size_kb,
                        "ruta": str(f)
                    })
            self.wfile.write(json.dumps(history, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"No encontrado")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/trace":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
                target = data.get("target", "").strip()
                if not target:
                    raise ValueError("URL o dominio vacío")
                result = trace_website(target)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silenciar logs ruidosos para una experiencia limpia
        pass

def run_server(port=PORT, open_browser=True):
    server = HTTPServer(("127.0.0.1", port), RequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print(f"🚀 Servidor de Rastreo Web iniciado con éxito!")
    print(f"🌐 Interfaz Visual disponible en: {url}")
    print(f"📂 Carpeta de reportes: {DEFAULT_OUTPUT_DIR}")
    print("=" * 60)
    print("Presiona Ctrl + C para detener el servidor.")

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()

if __name__ == "__main__":
    run_server()
