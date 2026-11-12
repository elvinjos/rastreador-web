<p align="center">
  <img src="assets/logo.svg" alt="Rastreador Web Logo" width="160" height="160">
</p>

<h1 align="center">🌐 Rastreador de Páginas Web</h1>

<p align="center">
  <strong>Herramienta integral de análisis, diagnóstico de red, seguridad SSL y auditoría web en tiempo real.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Licencia-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Dependencias-Zero%20(Stdlib)-brightgreen" alt="Dependencies">
  <img src="https://img.shields.io/badge/Plataforma-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey" alt="Platform">
</p>

---

## 📌 Tabla de Contenidos
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Instrucciones de Uso](#-instrucciones-de-uso)
  - [1. Lanzador Interactivo (Recomendado)](#1-lanzador-interactivo-recomendado)
  - [2. Modo Interfaz Gráfica Web](#2-modo-interfaz-gráfica-web)
  - [3. Modo Terminal (CLI)](#3-modo-terminal-cli)
- [Reportes Generados](#-reportes-generados)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Aviso Legal (Disclaimer)](#-aviso-legal-disclaimer)
- [Licencia](#-licencia)

---

## ✨ Características

- 🔍 **Inspección DNS y Red:** Resolución de direcciones IP, servidores DNS y verificación de latencia/conectividad.
- 🔒 **Auditoría SSL/TLS:** Análisis de validez de certificados, entidad emisora, cifrado y fechas de expiración.
- 🛡️ **Cabeceras de Seguridad:** Detección de `HSTS`, `CSP`, `X-Frame-Options`, `X-Content-Type-Options`, etc.
- 🌐 **Doble Modo de Operación:**
  - **Panel Web visual:** Dashboard interactivo en tu navegador local.
  - **Consola / CLI:** Para escaneos rápidos y automatización en servidores.
- 📄 **Exportación Automática:** Genera reportes detallados en formato `.json` (datos crudos) y `.md` (Markdown legible).
- ⚡ **Sin Dependencias Externas:** Desarrollado 100% con la biblioteca estándar de Python (`urllib`, `socket`, `ssl`, `http.server`). No requiere instalaciones complejas con `pip`.

---

## 📋 Requisitos

- **Python 3.8** o superior instalado en el sistema.
- Conexión a Internet.
- Navegador web moderno (para el panel gráfico).

---

## 🚀 Instalación

Clona el repositorio en tu máquina local:

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/rastreador-web.git

# 2. Entrar a la carpeta del proyecto
cd rastreador-web

# 3. Dar permisos de ejecución a los scripts
chmod +x iniciar_rastreador.sh rastreador.py
```

> **Nota:** No es necesario ejecutar `pip install` ya que el proyecto funciona íntegramente con los módulos nativos de Python.

---

## 💻 Instrucciones de Uso

Puedes utilizar el rastreador de tres formas distintas:

### 1. Lanzador Interactivo (Recomendado)
Ejecuta el asistente gráfico/menú en tu terminal:
```bash
./iniciar_rastreador.sh
```
Te presentará un menú interactivo:
```text
==================================================================
          🌐 BIENVENIDO AL RASTREADOR DE PÁGINAS WEB              
==================================================================
  [1] Modo Interfaz Web (Panel visual en tu navegador)
  [2] Modo Terminal (Escribir páginas directamente en la consola)
  [3] Abrir la carpeta de reportes guardados
  [4] Salir
==================================================================
```

---

### 2. Modo Interfaz Gráfica Web
Inicia el servidor local y abre el dashboard visual en tu navegador:
```bash
python3 rastreador.py --web
```
Por defecto se iniciará en `http://127.0.0.1:8888`. Si deseas cambiar el puerto:
```bash
python3 rastreador.py --web --port 9090
```

---

### 3. Modo Terminal (CLI)

* **Rastreo directo pasando la URL:**
  ```bash
  python3 rastreador.py https://ejemplo.com
  ```

* **Modo prompt (te pedirá ingresar la URL):**
  ```bash
  python3 rastreador.py
  ```

* **Ver ayuda de parámetros:**
  ```bash
  python3 rastreador.py --help
  ```

---

## 📊 Reportes Generados

Cada rastreo genera automáticamente dos archivos organizados en la carpeta `Rastreo de paginas web` dentro de tu directorio de usuario:
- `Rastreo_<dominio>_<fecha>.json`: Para integración con otras herramientas o análisis programático.
- `Rastreo_<dominio>_<fecha>.md`: Resumen ejecutivo formateado para lectura directa.

---

## 📁 Estructura del Proyecto

```text
rastreador-web/
├── assets/
│   └── logo.svg                 # Logo e identidad visual del repositorio
├── rastreador_web/
│   ├── app.py                   # Servidor web local y dashboard interactivo
│   └── tracer_core.py           # Motor de análisis de red, DNS, SSL y headers
├── iniciar_rastreador.sh         # Script Bash interactivo para Linux/macOS
├── rastreador.py                # Punto de entrada CLI y despachador
├── .gitignore                   # Archivos y carpetas ignorados por Git
├── LICENSE                      # Licencia de código abierto MIT
└── README.md                    # Documentación del proyecto
```

---

## 🖼️ ¿Cómo cambiar o personalizar el Logo?

Si quieres usar tu propia imagen o logotipo:
1. Coloca tu archivo de imagen (por ejemplo `mi_logo.png`) dentro de la carpeta `assets/`.
2. En la primera línea de este archivo `README.md`, cambia:
   ```html
   <img src="assets/logo.svg" alt="Rastreador Web Logo" width="160" height="160">
   ```
   por:
   ```html
   <img src="assets/mi_logo.png" alt="Mi Logo" width="160" height="160">
   ```

---

## ⚖️ Aviso Legal (Disclaimer)

Esta herramienta fue desarrollada con fines estrictamente educativos, de diagnóstico técnico y auditoría para desarrolladores y administradores de sistemas. El usuario asume toda la responsabilidad sobre el uso que le dé al software. Asegúrate de contar con la autorización correspondiente al analizar sitios web de terceros.

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
