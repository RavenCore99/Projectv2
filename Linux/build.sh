#!

# Script creado para build de codigo principal en python.
# dicho archivo esta hecho por librerias y a apoyo de foros e IA para la elaboracion del correcto funcionamiento
# replicar este .sh esta abierto al uso publico 

APP_NAME="ValidadorFacturas"
MAIN_SCRIPT="main.py"

echo "🔹 Limpiando compilaciones anteriores..."
rm -rf build dist __pycache__ *.spec

echo "🔹 Generando ejecutable con PyInstaller..."
python3 -m PyInstaller --onefile --windowed --name "$APP_NAME" "$MAIN_SCRIPT"


# Copiar el binario final a la carpeta actual
if [ -f "dist/$APP_NAME" ]; then
    echo "✅ Ejecución completada. Ejecutable disponible en: ./dist/$APP_NAME"
    echo "   Para ejecutarlo: ./dist/$APP_NAME"
else
    echo "❌ Error: No se generó el ejecutable."
    exit 1
fi

# Opcional: crear AppImage si tienes appimagetool instalado
if command -v appimagetool >/dev/null 2>&1; then
    echo "🔹 Creando AppImage..."
    mkdir -p AppDir/usr/bin
    cp dist/$APP_NAME AppDir/usr/bin/
    appimagetool AppDir "$APP_NAME-x86_64.AppImage"
    echo "✅ AppImage generado: $APP_NAME-x86_64.AppImage"
else
    echo "⚠️ appimagetool no está instalado. Si quieres AppImage ejecuta:"
    echo "   sudo apt install appimagetool -y"
fi
