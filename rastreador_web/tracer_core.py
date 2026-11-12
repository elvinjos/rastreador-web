#!/usr/bin/env python3
"""
Tracer Core - Motor de rastreo y análisis de páginas web.
Permite inspeccionar DNS, Geolocalización, ASN, Certificados SSL,
Cabeceras HTTP y evaluación de seguridad.
"""

import os
import sys
import re
import json
import socket
import ssl
from datetime import datetime, timezone
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path.home() / "Rastreo de paginas web"

def normalize_domain(raw_input: str) -> tuple[str, str]:
    """
    Normaliza una entrada (URL o dominio) devolviendo (clean_domain, full_url).
    """
    raw = raw_input.strip()
    if not raw:
        raise ValueError("La URL o dominio no puede estar vacío.")

    # Si no tiene protocolo, asumir https para probar
    if not re.match(r'^https?://', raw, re.IGNORECASE):
        test_url = "https://" + raw
    else:
        test_url = raw

    parsed = urllib.parse.urlparse(test_url)
    domain = parsed.hostname or raw.split('/')[0].split(':')[0]
    domain = domain.strip().lower()

    # Quitar puertos si vienen incluidos
    domain = domain.split(':')[0]

    return domain, test_url

def query_doh(domain: str, record_type: str = "A") -> list[str]:
    """Consulta registros DNS usando DNS-over-HTTPS (Google)."""
    try:
        url = f"https://dns.google/resolve?name={domain}&type={record_type}"
        req = urllib.request.Request(url, headers={"User-Agent": "WebTracer/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            answers = data.get("Answer", [])
            return [ans.get("data", "").strip('"') for ans in answers if "data" in ans]
    except Exception:
        return []

def get_dns_info(domain: str) -> dict:
    """Obtiene resolución IPv4, IPv6 y registros DNS vía DoH."""
    info = {
        "ipv4": [],
        "ipv6": [],
        "nameservers": [],
        "mx_records": [],
        "txt_records": [],
        "reverse_dns": {}
    }

    # IPv4 vía socket
    try:
        _, _, ips = socket.gethostbyname_ex(domain)
        info["ipv4"] = list(dict.fromkeys(ips))
    except Exception:
        # Fallback a DoH
        info["ipv4"] = query_doh(domain, "A")

    # IPv6 vía socket
    try:
        addrinfo = socket.getaddrinfo(domain, None, socket.AF_INET6)
        ipv6_list = [entry[4][0] for entry in addrinfo]
        info["ipv6"] = list(dict.fromkeys(ipv6_list))
    except Exception:
        info["ipv6"] = query_doh(domain, "AAAA")

    # Registros NS, MX, TXT
    info["nameservers"] = query_doh(domain, "NS")
    info["mx_records"] = query_doh(domain, "MX")
    info["txt_records"] = query_doh(domain, "TXT")

    # Reverse DNS para las IPs encontradas
    for ip in info["ipv4"]:
        try:
            rdns, _, _ = socket.gethostbyaddr(ip)
            info["reverse_dns"][ip] = rdns
        except Exception:
            info["reverse_dns"][ip] = "Sin registro PTR inverso"

    return info

def get_geoip_info(ip: str) -> dict:
    """Obtiene geolocalización, ASN e ISP de una IP."""
    if not ip:
        return {}

    # Intento 1: ip-api.com
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        req = urllib.request.Request(url, headers={"User-Agent": "WebTracer/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                return {
                    "ip": ip,
                    "pais": data.get("country", "Desconocido"),
                    "codigo_pais": data.get("countryCode", ""),
                    "region": data.get("regionName", ""),
                    "ciudad": data.get("city", "Desconocida"),
                    "codigo_postal": data.get("zip", ""),
                    "latitud": data.get("lat"),
                    "longitud": data.get("lon"),
                    "zona_horaria": data.get("timezone", ""),
                    "isp": data.get("isp", "Desconocido"),
                    "organizacion": data.get("org", "Desconocida"),
                    "asn": data.get("as", "Desconocido")
                }
    except Exception:
        pass

    # Intento 2: ipinfo.io como fallback
    try:
        url = f"https://ipinfo.io/{ip}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "WebTracer/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            loc = data.get("loc", "").split(",")
            lat = float(loc[0]) if len(loc) == 2 else None
            lon = float(loc[1]) if len(loc) == 2 else None
            return {
                "ip": ip,
                "pais": data.get("country", "Desconocido"),
                "codigo_pais": data.get("country", ""),
                "region": data.get("region", ""),
                "ciudad": data.get("city", "Desconocida"),
                "codigo_postal": data.get("postal", ""),
                "latitud": lat,
                "longitud": lon,
                "zona_horaria": data.get("timezone", ""),
                "isp": data.get("org", "Desconocido"),
                "organizacion": data.get("org", "Desconocida"),
                "asn": data.get("org", "Desconocido")
            }
    except Exception:
        pass

    return {
        "ip": ip,
        "pais": "No determinado",
        "ciudad": "No determinada",
        "isp": "No determinado",
        "organizacion": "No determinada",
        "asn": "No determinado"
    }

def get_ssl_info(domain: str) -> dict:
    """Inspecciona el certificado SSL/TLS del dominio."""
    info = {
        "disponible": False,
        "emisor": "No disponible",
        "emisor_org": "No disponible",
        "sujeto": "No disponible",
        "valido_desde": None,
        "valido_hasta": None,
        "dias_restantes": None,
        "expirado": False,
        "dominios_san": [],
        "error": None
    }

    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(6)
            s.connect((domain, 443))
            cert = s.getpeercert()

            issuer_dict = dict(x[0] for x in cert.get("issuer", []))
            subject_dict = dict(x[0] for x in cert.get("subject", []))

            info["disponible"] = True
            info["emisor"] = issuer_dict.get("commonName", "Desconocido")
            info["emisor_org"] = issuer_dict.get("organizationName", issuer_dict.get("commonName", "Desconocido"))
            info["sujeto"] = subject_dict.get("commonName", domain)

            # Fechas de expiración
            date_fmt = r"%b %d %H:%M:%S %Y %Z"
            not_after_str = cert.get("notAfter")
            not_before_str = cert.get("notBefore")

            if not_after_str:
                exp_dt = datetime.strptime(not_after_str, date_fmt).replace(tzinfo=timezone.utc)
                now_dt = datetime.now(timezone.utc)
                info["valido_hasta"] = exp_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                dias = (exp_dt - now_dt).days
                info["dias_restantes"] = dias
                info["expirado"] = dias < 0

            if not_before_str:
                start_dt = datetime.strptime(not_before_str, date_fmt).replace(tzinfo=timezone.utc)
                info["valido_desde"] = start_dt.strftime("%Y-%m-%d %H:%M:%S UTC")

            info["dominios_san"] = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"]

    except ssl.SSLCertVerificationError as e:
        info["error"] = f"Certificado no válido o auto-firmado: {e.reason}"
    except Exception as e:
        info["error"] = str(e)

    return info

def get_http_info(domain: str) -> dict:
    """Inspecciona cabeceras HTTP, servidor, redirecciones y seguridad."""
    info = {
        "status_code": None,
        "url_final": None,
        "redirecciones": [],
        "servidor": "Oculto / No especificado",
        "via": None,
        "cdn": "No detectado",
        "seguridad_cabeceras": {
            "hsts": False,
            "csp": False,
            "x_frame_options": False,
            "x_content_type_options": False,
            "referrer_policy": False
        },
        "detalles_cabeceras": {},
        "error": None
    }

    class RedirectTracker(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            info["redirecciones"].append({"codigo": code, "destino": newurl})
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(RedirectTracker)
    # Probar primero HTTPS
    urls_to_try = [f"https://{domain}", f"http://{domain}"]

    for url in urls_to_try:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                }
            )
            with opener.open(req, timeout=7) as resp:
                info["status_code"] = resp.status
                info["url_final"] = resp.geturl()
                headers = dict(resp.headers)
                info["detalles_cabeceras"] = headers

                # Identificar servidor y proxy
                info["servidor"] = headers.get("Server", headers.get("server", "No especificado"))
                info["via"] = headers.get("Via", headers.get("via", None))

                # Detección CDN
                h_str = " ".join([f"{k}:{v}" for k, v in headers.items()]).lower()
                if "cloudflare" in h_str or "cf-ray" in h_str:
                    info["cdn"] = "Cloudflare"
                elif "akamai" in h_str:
                    info["cdn"] = "Akamai"
                elif "cloudfront" in h_str or "x-amz-cf-id" in h_str:
                    info["cdn"] = "Amazon CloudFront"
                elif "fastly" in h_str:
                    info["cdn"] = "Fastly"
                elif "sucuri" in h_str:
                    info["cdn"] = "Sucuri Firewall"
                elif "incapsula" in h_str:
                    info["cdn"] = "Imperva / Incapsula"

                # Análisis de Cabeceras de Seguridad
                sec = info["seguridad_cabeceras"]
                sec["hsts"] = any(k.lower() == "strict-transport-security" for k in headers)
                sec["csp"] = any(k.lower() == "content-security-policy" for k in headers)
                sec["x_frame_options"] = any(k.lower() == "x-frame-options" for k in headers)
                sec["x_content_type_options"] = any(k.lower() == "x-content-type-options" for k in headers)
                sec["referrer_policy"] = any(k.lower() == "referrer-policy" for k in headers)

                break
        except urllib.error.HTTPError as e:
            info["status_code"] = e.code
            info["error"] = f"Respuesta HTTP {e.code}: {e.reason}"
            break
        except Exception as e:
            info["error"] = str(e)
            continue

    return info

def evaluate_security(domain: str, dns_info: dict, geo_info: dict, ssl_info: dict, http_info: dict) -> dict:
    """Evalúa la seguridad global del sitio web y emite un nivel de riesgo."""
    puntos_confianza = 50
    alertas_riesgo = []
    puntos_favorables = []

    # 1. SSL
    if ssl_info.get("disponible"):
        puntos_confianza += 25
        puntos_favorables.append(f"Cifrado SSL activo y emitido por entidad reconocida ({ssl_info.get('emisor_org')}).")
        if ssl_info.get("expirado"):
            puntos_confianza -= 35
            alertas_riesgo.append("El certificado SSL está CADUCADO.")
        elif ssl_info.get("dias_restantes") is not None and ssl_info.get("dias_restantes") < 7:
            puntos_confianza -= 10
            alertas_riesgo.append(f"El certificado SSL expirará pronto (quedan {ssl_info.get('dias_restantes')} días).")
    else:
        puntos_confianza -= 30
        alertas_riesgo.append("No cuenta con certificado SSL válido o la conexión HTTPS falló.")

    # 2. Cabeceras de seguridad
    sec = http_info.get("seguridad_cabeceras", {})
    if sec.get("hsts"):
        puntos_confianza += 5
        puntos_favorables.append("Implementa HSTS (fuerza siempre navegación segura HTTPS).")
    else:
        alertas_riesgo.append("Falta cabecera HSTS (Strict-Transport-Security).")

    if sec.get("csp"):
        puntos_confianza += 5
        puntos_favorables.append("Implementa CSP (protección contra inyecciones de código XSS).")
    else:
        alertas_riesgo.append("Falta cabecera Content-Security-Policy (CSP).")

    if sec.get("x_frame_options"):
        puntos_confianza += 5
        puntos_favorables.append("Implementa protección anti-Clickjacking (X-Frame-Options).")

    # 3. CDN y Anti-DDoS
    if http_info.get("cdn") != "No detectado":
        puntos_confianza += 10
        puntos_favorables.append(f"Utiliza protección CDN/WAF ({http_info.get('cdn')}) para mitigar ataques.")

    # 4. Análisis de Origen y Jurisdicción
    pais = geo_info.get("pais", "")
    org = geo_info.get("organizacion", "") + " " + geo_info.get("isp", "")
    jurisdicciones_offshore = ["Curacao", "Curaçao", "Cyprus", "Chipre", "Malta", "Belize", "Seychelles", "Gibraltar", "Panama", "Bahamas"]
    es_offshore = any(j.lower() in pais.lower() for j in jurisdicciones_offshore)

    if es_offshore:
        alertas_riesgo.append(f"Alojado o procesado en jurisdicción offshore ({pais} / {geo_info.get('ciudad')}), común en casinos, casas de apuestas o entidades con baja regulación financiera.")

    # 5. Detección de palabras clave en el dominio
    palabras_riesgo = ["win", "bet", "casino", "poker", "free-crypto", "airdrop", "login-verify", "bank-update"]
    if any(p in domain for p in palabras_riesgo):
        alertas_riesgo.append("El nombre de dominio coincide con patrones comunes de plataformas de apuestas o páginas de alto escrutinio.")

    # Normalizar puntaje 0 a 100
    puntos_confianza = max(10, min(100, puntos_confianza))

    if puntos_confianza >= 75 and len(alertas_riesgo) <= 2:
        nivel_riesgo = "BAJO"
        color = "green"
        resumen = "El sitio web es técnicamente seguro para navegar. Presenta cifrado y protecciones de infraestructura adecuadas."
    elif puntos_confianza >= 45:
        nivel_riesgo = "MEDIO (Precaución)"
        color = "yellow"
        resumen = "El sitio es accesible y cifrado, pero presenta características que ameritan precaución (jurisdicción offshore, falta de ciertas cabeceras de seguridad o naturaleza del negocio)."
    else:
        nivel_riesgo = "ALTO"
        color = "red"
        resumen = "Riesgo elevado. Carece de certificaciones de seguridad adecuadas, certificado vencido o indicios sospechosos."

    return {
        "puntuacion": puntos_confianza,
        "nivel_riesgo": nivel_riesgo,
        "color": color,
        "resumen": resumen,
        "alertas_riesgo": alertas_riesgo,
        "puntos_favorables": puntos_favorables
    }

def trace_website(target: str, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict:
    """
    Ejecuta el rastreo integral de una página web y genera el reporte.
    """
    domain, full_url = normalize_domain(target)
    fecha_analisis = datetime.now()
    timestamp_str = fecha_analisis.strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = fecha_analisis.strftime("%Y%m%d_%H%M%S")

    # 1. DNS
    dns_info = get_dns_info(domain)

    # 2. GeoIP (primera IP)
    primary_ip = dns_info["ipv4"][0] if dns_info["ipv4"] else ""
    geo_info = get_geoip_info(primary_ip)

    # 3. SSL
    ssl_info = get_ssl_info(domain)

    # 4. HTTP Headers
    http_info = get_http_info(domain)

    # 5. Evaluación de Seguridad
    seguridad = evaluate_security(domain, dns_info, geo_info, ssl_info, http_info)

    report_data = {
        "dominio": domain,
        "url_solicitada": target,
        "url_final": http_info.get("url_final") or full_url,
        "fecha": timestamp_str,
        "ip_principal": primary_ip,
        "geolocalizacion": geo_info,
        "dns": dns_info,
        "ssl": ssl_info,
        "http": http_info,
        "seguridad": seguridad
    }

    # Guardar reportes en la carpeta personal especificada
    output_dir.mkdir(parents=True, exist_ok=True)

    sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', domain)
    md_filename = output_dir / f"Rastreo_{sanitized_name}_{file_timestamp}.md"
    json_filename = output_dir / f"Rastreo_{sanitized_name}_{file_timestamp}.json"

    # Generar contenido Markdown
    md_content = generate_markdown_report(report_data)
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Generar contenido JSON
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    report_data["archivos_guardados"] = {
        "markdown": str(md_filename),
        "json": str(json_filename)
    }

    return report_data

def generate_markdown_report(data: dict) -> str:
    """Genera un reporte Markdown limpio y estructurado."""
    geo = data["geolocalizacion"]
    ssl = data["ssl"]
    http = data["http"]
    dns = data["dns"]
    seg = data["seguridad"]

    md = f"""# 🌐 Reporte de Rastreo Web: `{data['dominio']}`
> **Fecha de análisis:** {data['fecha']}  
> **URL analizada:** {data['url_solicitada']}  
> **URL destino final:** {data['url_final']}  

---

## 🛡️ 1. Diagnóstico de Seguridad y Veredicto

| Parámetro | Detalle |
| :--- | :--- |
| **Nivel de Riesgo** | **{seg['nivel_riesgo']}** |
| **Puntaje de Confianza** | `{seg['puntuacion']} / 100` |
| **Cifrado SSL/TLS** | {'✅ Activo y Válido' if ssl.get('disponible') and not ssl.get('expirado') else '❌ Inseguro / Expirado'} |
| **Red de Protección / CDN** | `{http.get('cdn')}` |
| **Servidor Detectado** | `{http.get('servidor')}` |

**Resumen:**  
{seg['resumen']}

### ⚠️ Observaciones y Factores de Riesgo:
"""
    if seg["alertas_riesgo"]:
        for a in seg["alertas_riesgo"]:
            md += f"- ⚠️ {a}\n"
    else:
        md += "- ✅ No se detectaron anomalías críticas evidentes.\n"

    md += "\n### ✅ Puntos Favorables:\n"
    if seg["puntos_favorables"]:
        for p in seg["puntos_favorables"]:
            md += f"- ✔️ {p}\n"
    else:
        md += "- Ningún factor relevante favorable registrado.\n"

    md += f"""
---

## 🌍 2. Ubicación Geográfica y Origen de la Red

* **Dirección IP principal:** `{data['ip_principal']}`
* **País:** {geo.get('pais')} ({geo.get('codigo_pais')})
* **Ciudad / Región:** {geo.get('ciudad')}, {geo.get('region')}
* **Organización / Propietario:** **{geo.get('organizacion')}**
* **Proveedor de Internet (ISP):** `{geo.get('isp')}`
* **Sistema Autónomo (ASN):** `{geo.get('asn')}`
* **Zona Horaria:** `{geo.get('zona_horaria')}`
"""
    if geo.get("latitud") and geo.get("longitud"):
        md += f"* **Coordenadas aproximadas:** `{geo.get('latitud')}, {geo.get('longitud')}`\n"
        md += f"* [Ver ubicación en OpenStreetMap](https://www.openstreetmap.org/?mlat={geo.get('latitud')}&mlon={geo.get('longitud')}#map=12/{geo.get('latitud')}/{geo.get('longitud')})\n"

    md += f"""
---

## 🔒 3. Certificado de Seguridad (SSL / HTTPS)

* **Estado:** {'Válido' if ssl.get('disponible') and not ssl.get('expirado') else 'No disponible o con error'}
* **Entidad Emisora (CA):** `{ssl.get('emisor_org')}` (`{ssl.get('emisor')}`)
* **Titular / Sujeto:** `{ssl.get('sujeto')}`
* **Válido desde:** `{ssl.get('valido_desde')}`
* **Válido hasta:** `{ssl.get('valido_hasta')}`
* **Días de vigencia restantes:** `{ssl.get('dias_restantes')} días`
* **Dominios alternativos (SAN):** {', '.join(ssl.get('dominios_san', [])[:5])}{' (y más...)' if len(ssl.get('dominios_san', [])) > 5 else ''}
"""

    md += f"""
---

## 📡 4. Infraestructura DNS

* **Direcciones IPv4:** `{', '.join(dns.get('ipv4', [])) or 'No encontradas'}`
* **Direcciones IPv6:** `{', '.join(dns.get('ipv6', [])) or 'No disponibles'}`
* **Servidores de Nombres (NS):**
"""
    for ns in dns.get("nameservers", []):
        md += f"  - `{ns}`\n"
    if not dns.get("nameservers"):
        md += "  - *Sin registros NS disponibles*\n"

    md += "\n* **Servidores de Correo (MX):**\n"
    for mx in dns.get("mx_records", []):
        md += f"  - `{mx}`\n"
    if not dns.get("mx_records"):
        md += "  - *Sin registros MX configurados*\n"

    md += f"""
---

## ⚙️ 5. Cabeceras HTTP y Tecnologías

* **Código de respuesta:** `{http.get('status_code')}`
* **Servidor Web:** `{http.get('servidor')}`
* **Cabecera Via / Proxy:** `{http.get('via') or 'Ninguna'}`
* **Red CDN:** `{http.get('cdn')}`

### Cabeceras de Seguridad del Navegador:
* **HSTS (Conexión estricta HTTPS):** {'✅ Presente' if http['seguridad_cabeceras']['hsts'] else '❌ Ausente'}
* **CSP (Content-Security-Policy):** {'✅ Presente' if http['seguridad_cabeceras']['csp'] else '❌ Ausente'}
* **X-Frame-Options (Anti-Clickjacking):** {'✅ Presente' if http['seguridad_cabeceras']['x_frame_options'] else '❌ Ausente'}
* **X-Content-Type-Options:** {'✅ Presente' if http['seguridad_cabeceras']['x_content_type_options'] else '❌ Ausente'}

---
*Reporte generado automáticamente por la aplicación de Rastreo Web.*
"""
    return md

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "1win.lat"
    print(f"Rastreando {target}...")
    resultado = trace_website(target)
    print("Reporte generado:")
    print(" - Markdown:", resultado["archivos_guardados"]["markdown"])
    print(" - JSON:", resultado["archivos_guardados"]["json"])
    print(f"Nivel de Riesgo: {resultado['seguridad']['nivel_riesgo']} (Puntaje: {resultado['seguridad']['puntuacion']}/100)")
    print(f"Origen: {resultado['geolocalizacion'].get('pais')} - {resultado['geolocalizacion'].get('organizacion')}")
