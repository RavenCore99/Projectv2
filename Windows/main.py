#Se agregan las librerias correspondientes al codigo para facilitar la ejecucion de la solicitud 
# dicho codigo hacer parte del prototipo para verificacion de facturas por medio de digitos numericos
# basado en las expresiones regulares de la teoria de lenguajes y automatas
# --------------- Prototipo elaborado por el Grupo A -------------------------------------------------

import re
import tkinter as tk
from tkinter import messagebox

class ValidadorFactura:
    regex_nit = re.compile(r"^\d{6,10}-\d$")
    regex_fecha = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
    regex_valor = re.compile(r"^\d+(\.\d{1,2})?$")

    @staticmethod
    def validar_nit(nit: str) -> bool:
        return bool(ValidadorFactura.regex_nit.match(nit))

    @staticmethod
    def validar_fecha(fecha: str) -> bool:
        return bool(ValidadorFactura.regex_fecha.match(fecha))

    @staticmethod
    def validar_valor(valor: str) -> bool:
        return bool(ValidadorFactura.regex_valor.match(valor))

    @staticmethod
    def validar_factura(factura: dict) -> dict:
        return {
            "NIT válido": ValidadorFactura.validar_nit(factura.get("nit", "")),
            "Fecha válida": ValidadorFactura.validar_fecha(factura.get("fecha", "")),
            "Valor válido": ValidadorFactura.validar_valor(factura.get("valor", ""))
        }


# ---------------- Interfaz gráfica ----------------

def guardar_factura():
    nit = entry_nit.get().strip()
    fecha = entry_fecha.get().strip()
    valor = entry_valor.get().strip()

    factura = {"nit": nit, "fecha": fecha, "valor": valor}
    resultado = ValidadorFactura.validar_factura(factura)

    # Verifica si los campos son validos
    factura_valida = all(resultado.values())

    # mensaje reflejado
    mensaje = f"Factura ingresada:\nNIT: {nit}\nFecha: {fecha}\nValor: {valor}\n\n"
    for campo, valido in resultado.items():
        mensaje += f"{campo}: {'✔️' if valido else '❌'}\n"

    if factura_valida:
        mensaje += "\n✅ Factura válida"
    else:
        mensaje += "\n❌ Factura inválida"

    # Mostrar mensaje en GUI
    messagebox.showinfo("Resultado de validación", mensaje)

    # Guardar en archivo
    with open("facturas_registro.txt", "a", encoding="utf-8") as f:
        f.write(mensaje + "\n" + "-"*50 + "\n")


# ----------------  GUI Por la libreria tkinter  ----------------
root = tk.Tk()
root.title("Validador de Facturación Electrónica")
root.geometry("400x300")
root.resizable(False, False)

# Etiquetas y entradas
tk.Label(root, text="Ingrese NIT (formato: 123456789-0):").pack(pady=5)
entry_nit = tk.Entry(root, width=30)
entry_nit.pack(pady=5)

tk.Label(root, text="Ingrese Fecha (YYYY-MM-DD):").pack(pady=5)
entry_fecha = tk.Entry(root, width=30)
entry_fecha.pack(pady=5)

tk.Label(root, text="Ingrese Valor (ej: 1500.50):").pack(pady=5)
entry_valor = tk.Entry(root, width=30)
entry_valor.pack(pady=5)

# Botón para validar y guardar
btn_validar = tk.Button(root, text="Validar y Guardar Factura", command=guardar_factura)
btn_validar.pack(pady=20)

# Ejecutar interfaz
root.mainloop()
