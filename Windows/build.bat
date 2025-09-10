@echo off
SET APP_NAME=ValidadorFacturas
SET MAIN_SCRIPT=main.py
SET REGISTRO=facturas_registro.txt

echo 🔹 Limpiando compilaciones anteriores...
rmdir /S /Q build dist
del %APP_NAME%.spec

echo 🔹 Generando ejecutable con PyInstaller...
python -m PyInstaller --onefile --windowed --name %APP_NAME% %MAIN_SCRIPT%

IF EXIST dist\%APP_NAME%.exe (
    echo ✅ Ejecución completada. Ejecutable disponible en: dist\%APP_NAME%.exe

    REM Copiar archivo de registro si existe
    IF EXIST %REGISTRO% (
        copy %REGISTRO% dist\
        echo 📂 Archivo %REGISTRO% copiado a dist\
    ) ELSE (
        echo ⚠️ No se encontró %REGISTRO%, se creará vacío.
        echo > dist\%REGISTRO%
    )

    echo 🎉 Distribución lista en la carpeta: dist\
) ELSE (
    echo ❌ Error: No se generó el ejecutable.
)
pause
