#!/usr/bin/env python3
"""
Rastreador de Páginas Web - CLI Interactivo y Lanzador
Permite rastrear cualquier sitio web, inspeccionar su origen, seguridad y guardar el reporte
automáticamente en la carpeta personal 'Rastreo de paginas web'.
"""

import sys
import os
import argparse
from pathlib import Path

# Añadir el directorio del motor al sys.path
BASE_DIR = Path(__file__).resolve().parent / "rastreador_web"
sys.path.insert(0, str(BASE_DIR))

try:
    from tracer_core import trace_website, DEFAULT_OUTPUT_DIR
except ImportError:
    # Si se ejecuta dentro de rastreador_web
    from rastreador_web.tracer_core import trace_website, DEFAULT_OUTPUT_DIR

# Códigos de color ANSI para la terminal
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_GRAY = "\033[90m"

def print_banner():
    banner = f"""
{C_CYAN}{C_BOLD}╔════════════════════════════════════════════════════════════════════╗
║                🌐 RASTREADOR DE PÁGINAS WEB                        ║
║          Inspección de Origen, Infraestructura y Seguridad         ║
╚════════════════════════════════════════════════════════════════════╝{C_RESET}
{C_GRAY}📁 Reportes guardados en: {DEFAULT_OUTPUT_DIR}{C_RESET}
"""
    print(banner)

def print_summary(data: dict):
    geo = data.get("geolocalizacion", {})
    ssl_info = data.get("ssl", {})
    http = data.get("http", {})
    seg = data.get("seguridad", {})

    print("\n" + "=" * 65)
    print(f"{C_BOLD}RESULTADOS DEL RASTREO PARA:{C_RESET} {C_CYAN}{data['dominio']}{C_RESET}")
    print("=" * 65)

    # Nivel de Riesgo
    color_riesgo = C_GREEN if "BAJO" in seg["nivel_riesgo"] else (C_YELLOW if "MEDIO" in seg["nivel_riesgo"] else C_RED)
    print(f"\n{C_BOLD}🛡️  SEGURIDAD Y RIESGO:{C_RESET}")
    print(f"  • Nivel de Riesgo:     {color_riesgo}{C_BOLD}{seg['nivel_riesgo']}{C_RESET}")
    print(f"  • Puntaje Confianza:   {C_BOLD}{seg['puntuacion']} / 100{C_RESET}")
    print(f"  • Diagnóstico:         {seg['resumen']}")

    if seg.get("alertas_riesgo"):
        print(f"\n  {C_YELLOW}{C_BOLD}Alertas detectadas:{C_RESET}")
        for alerta in seg["alertas_riesgo"]:
            print(f"   {C_YELLOW}⚠️  {alerta}{C_RESET}")

    if seg.get("puntos_favorables"):
        print(f"\n  {C_GREEN}{C_BOLD}Factores favorables:{C_RESET}")
        for punto in seg["puntos_favorables"]:
            print(f"   {C_GREEN}✔️  {punto}{C_RESET}")

    # Origen
    print(f"\n{C_BOLD}🌍  ORIGEN Y PROPIETARIO:{C_RESET}")
    print(f"  • País / Ciudad:       {C_BOLD}{geo.get('pais', 'Desconocido')} ({geo.get('codigo_pais', '')}) - {geo.get('ciudad', '')}{C_RESET}")
    print(f"  • Organización:        {C_CYAN}{geo.get('organizacion', 'Desconocida')}{C_RESET}")
    print(f"  • Proveedor (ISP):     {geo.get('isp', 'Desconocido')}")
    print(f"  • Sistema Autónomo:    {geo.get('asn', 'Desconocido')}")
    print(f"  • IP Principal:        {C_BOLD}{data.get('ip_principal')}{C_RESET}")

    # SSL
    print(f"\n{C_BOLD}🔒  CERTIFICADO SSL/TLS:{C_RESET}")
    ssl_status = f"{C_GREEN}Válido{C_RESET}" if ssl_info.get("disponible") and not ssl_info.get("expirado") else f"{C_RED}Inválido o No disponible{C_RESET}"
    print(f"  • Estado:              {ssl_status}")
    print(f"  • Emisor:              {ssl_info.get('emisor_org', 'Desconocido')}")
    print(f"  • Vence en:            {ssl_info.get('dias_restantes')} días ({ssl_info.get('valido_hasta')})")

    # Servidor / CDN
    print(f"\n{C_BOLD}⚙️   INFRAESTRUCTURA TÉCNICA:{C_RESET}")
    print(f"  • Servidor Web:        {http.get('servidor')}")
    print(f"  • Red CDN:             {http.get('cdn')}")
    print(f"  • URL Final:           {data.get('url_final')}")

    # Archivos guardados
    print("\n" + "-" * 65)
    print(f"{C_GREEN}{C_BOLD}✅ ARCHIVOS GENERADOS Y GUARDADOS EN TU CARPETA PERSONAL:{C_RESET}")
    print(f"  📄 Reporte Markdown:   {C_CYAN}{data['archivos_guardados']['markdown']}{C_RESET}")
    print(f"  📊 Datos JSON:         {C_CYAN}{data['archivos_guardados']['json']}{C_RESET}")
    print("-" * 65 + "\n")

def run_cli_interactive():
    print_banner()
    while True:
        try:
            target = input(f"{C_BOLD}Ingresa la URL o página a rastrear (o 's' para salir): {C_RESET}").strip()
            if not target:
                continue
            if target.lower() in ["s", "salir", "exit", "quit", "q"]:
                print(f"\n{C_BLUE}¡Hasta pronto!{C_RESET}\n")
                break

            print(f"\n{C_CYAN}⏳ Rastreando e inspeccionando {target}... Por favor espera unos segundos.{C_RESET}")
            resultado = trace_website(target)
            print_summary(resultado)

        except KeyboardInterrupt:
            print(f"\n\n{C_BLUE}Operación cancelada. ¡Hasta pronto!{C_RESET}\n")
            break
        except Exception as e:
            print(f"\n{C_RED}❌ Error al rastrear:{C_RESET} {e}\n")

def main():
    parser = argparse.ArgumentParser(description="Rastreador y Verificador de Páginas Web")
    parser.add_argument("url", nargs="?", help="URL o dominio de la página a rastrear (opcional)")
    parser.add_argument("--web", action="store_true", help="Iniciar la interfaz gráfica web en el navegador")
    parser.add_argument("--port", type=int, default=8888, help="Puerto para el servidor web (por defecto: 8888)")

    args = parser.parse_args()

    if args.web:
        from app import run_server
        run_server(port=args.port)
    elif args.url:
        print_banner()
        print(f"{C_CYAN}⏳ Rastreando e inspeccionando {args.url}...{C_RESET}")
        try:
            resultado = trace_website(args.url)
            print_summary(resultado)
        except Exception as e:
            print(f"\n{C_RED}❌ Error al rastrear:{C_RESET} {e}\n")
            sys.exit(1)
    else:
        run_cli_interactive()

if __name__ == "__main__":
    main()
