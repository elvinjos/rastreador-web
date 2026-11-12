#!/usr/bin/env bash
# ==============================================================================
# Lanzador del Rastreador de Páginas Web
# ==============================================================================

DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3)"

if [ -z "$PYTHON_BIN" ]; then
    echo "Error: Python 3 no está instalado en el sistema."
    exit 1
fi

# Si se pasó una URL como argumento, ejecutar directamente
if [ -n "$1" ]; then
    "$PYTHON_BIN" "$DIR_SCRIPT/rastreador.py" "$1"
    exit 0
fi

clear
echo "=================================================================="
echo "          🌐 BIENVENIDO AL RASTREADOR DE PÁGINAS WEB              "
echo "=================================================================="
echo " Carpeta de reportes: $HOME/Rastreo de paginas web"
echo "=================================================================="
echo ""
echo " Selecciona cómo deseas usar el aplicativo:"
echo ""
echo "  [1] Modo Interfaz Web (Panel visual en tu navegador)"
echo "  [2] Modo Terminal (Escribir páginas directamente en la consola)"
echo "  [3] Abrir la carpeta de reportes guardados"
echo "  [4] Salir"
echo ""
read -p " Ingresa una opción [1-4]: " OPCION

case "$OPCION" in
    1)
        echo ""
        echo " Iniciando servidor web..."
        echo " Abre tu navegador en: http://127.0.0.1:8888"
        if which xdg-open > /dev/null 2>&1; then
            (sleep 1 && xdg-open "http://127.0.0.1:8888") &
        fi
        "$PYTHON_BIN" "$DIR_SCRIPT/rastreador.py" --web
        ;;
    2)
        "$PYTHON_BIN" "$DIR_SCRIPT/rastreador.py"
        ;;
    3)
        CARPETA="$HOME/Rastreo de paginas web"
        mkdir -p "$CARPETA"
        if which xdg-open > /dev/null 2>&1; then
            xdg-open "$CARPETA"
        else
            ls -la "$CARPETA"
        fi
        ;;
    4)
        echo "¡Hasta luego!"
        exit 0
        ;;
    *)
        echo "Opción no válida. Ejecutando en modo terminal por defecto..."
        "$PYTHON_BIN" "$DIR_SCRIPT/rastreador.py"
        ;;
esac
