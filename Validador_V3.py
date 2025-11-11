# Nicolas C. Baññesteros  / Etham Torres
# dicho codigo hacer parte del prototipo para verificacion de facturas por medio de digitos numericos
# basado en las expresiones regulares de la teoria de lenguajes y automatas
# --------------- Prototipo elaborado por el Grupo A -------------------------------------------------

import re
import sqlite3
import csv
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from tkcalendar import Calendar


# ======================  AUTÓMATAS definidos ======================
class AutomataValidador:
    _re_nit = re.compile(r"^\d{6,10}-\d$")
    _re_fecha = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
    _re_valor = re.compile(r"^\d+(\.\d{1,2})?$")
    _re_usuario = re.compile(r"^[a-zA-Z0-9_]{4,20}$")

    @staticmethod
    def nit(nit: str) -> bool:
        return bool(AutomataValidador._re_nit.fullmatch(nit))

    @staticmethod
    def fecha(fecha: str) -> bool:
        return bool(AutomataValidador._re_fecha.fullmatch(fecha))

    @staticmethod
    def valor(valor: str) -> bool:
        return bool(AutomataValidador._re_valor.fullmatch(valor))

    @staticmethod
    def usuario(usuario: str) -> bool:
        return bool(AutomataValidador._re_usuario.fullmatch(usuario))


# ====================== SQLITE3 ======================
class GestorDB:
    _DB_FILE = "facturacion.db"
    IVA_RATE = 0.19  # 19% IVA Colombia

    def __init__(self):
        self.conn = sqlite3.connect(self._DB_FILE)
        self._crear_esquemas()
        self._cargar_datos_iniciales()

    def _crear_esquemas(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS producto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL CHECK(precio >= 0),
                categoria_id INTEGER,
                UNIQUE(nombre, categoria_id),
                FOREIGN KEY(categoria_id) REFERENCES categoria(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cliente (
                nit TEXT PRIMARY KEY,
                nombre TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS factura (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nit TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                usuario TEXT NOT NULL,
                subtotal REAL NOT NULL,
                iva REAL NOT NULL,
                total REAL NOT NULL,
                valido INTEGER NOT NULL,
                FOREIGN KEY(nit) REFERENCES cliente(nit)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detalle_factura (
                factura_id INTEGER,
                producto_id INTEGER,
                cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                subtotal REAL NOT NULL,
                iva REAL NOT NULL,
                total REAL NOT NULL,
                FOREIGN KEY(factura_id) REFERENCES factura(id),
                FOREIGN KEY(producto_id) REFERENCES producto(id)
            )
        """)
        self.conn.commit()

    def _cargar_datos_iniciales(self):
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO categoria (nombre) VALUES (?)", ("Electrónica General",))
        cat_id = cur.execute("SELECT id FROM categoria WHERE nombre = ?", ("Electrónica General",)).fetchone()[0]

        productos_electronica = [
            ("Kit herramientas", 250000.0), ("Kit Electronica", 350000.0), ("Disco SSD 250GB", 150000.0),
            ("Audifonos Gamer", 200000.0), ("Monitor 144Hz 2k", 1500000.0), ("Monitor 240Hz 4k", 2300000.0),
            ("Mouse Logitech G710 Air", 450000.0), ("Chasis Aerocool ATX", 650000.0),
            ("Teclado Razer Viper x10", 350000.0), ("Teclado membrana logitech", 80000.0),
            ("kit teclado/mouse Logitech oficina", 120000.0), ("kit RAM x2 16GB 3600MHz", 420000.0),
            ("Disco HDD 1TB SeaGate", 220000.0), ("Grafica GTX 1660 SUPER 6GB VRAM", 950000.0),
            ("Grafica RTX 2080 Ti 8GB VRAM", 1600000.0), ("Grafica RTX 3090 12GB VRAM", 2250000.0),
            ("Grafica RTX 4090 16GB VRAM", 4650000.0), ("Grafica RTX 5090 24GB VRAM", 12000000.0),
            ("Preocesador Intel i9 12 generacion", 6000000.0), ("Procesador Ryzen 7 7900 x", 4300000.0),
            ("Procesador Intel i7 11 generacion", 670000.0), ("Procesador Ryzen 5 4600G", 560000.0),
        ]
        for nombre, precio in productos_electronica:
            cur.execute("INSERT OR IGNORE INTO producto (nombre, precio, categoria_id) VALUES (?, ?, ?)",
                        (nombre, precio, cat_id))
        cur.execute("INSERT OR IGNORE INTO admin (usuario, password) VALUES (?, ?)", ("admin", "admin123"))
        self.conn.commit()

    def login(self, usuario: str, password: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM admin WHERE usuario = ? AND password = ?", (usuario, password))
        return cur.fetchone() is not None

    def agregar_admin(self, usuario: str, password: str) -> bool:
        if not (AutomataValidador.usuario(usuario) and len(password) >= 6):
            return False
        try:
            self.conn.execute("INSERT INTO admin (usuario, password) VALUES (?, ?)", (usuario, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def reset_password(self, usuario: str, new_password: str) -> bool:
        if not (AutomataValidador.usuario(usuario) and len(new_password) >= 6):
            return False
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM admin WHERE usuario = ?", (usuario,))
        if cur.fetchone():
            cur.execute("UPDATE admin SET password = ? WHERE usuario = ?", (new_password, usuario))
            self.conn.commit()
            return True
        return False

    def listar_categorias(self) -> List[Tuple[int, str]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, nombre FROM categoria ORDER BY nombre")
        return cur.fetchall()

    def listar_productos(self, categoria_id: Optional[int] = None) -> List[Tuple[int, str, float, str]]:
        cur = self.conn.cursor()
        query = """
            SELECT p.id, p.nombre, p.precio, c.nombre
            FROM producto p JOIN categoria c ON p.categoria_id = c.id
        """
        params = []
        if categoria_id:
            query += " WHERE p.categoria_id = ?"
            params.append(categoria_id)
        query += " ORDER BY c.nombre, p.nombre"
        cur.execute(query, params)
        return cur.fetchall()

    def agregar_producto(self, nombre: str, precio: float, categoria_id: int) -> bool:
        try:
            self.conn.execute("INSERT INTO producto (nombre, precio, categoria_id) VALUES (?, ?, ?)",
                             (nombre, precio, categoria_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def registrar_cliente(self, nit: str, nombre: str) -> bool:
        try:
            self.conn.execute("INSERT INTO cliente (nit, nombre) VALUES (?, ?)", (nit, nombre))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def guardar_factura(self, nit: str, fecha: str, hora: str, usuario: str, items: List[Dict], subtotal: float, iva: float, total: float, valido: bool):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO factura (nit, fecha, hora, usuario, subtotal, iva, total, valido)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nit, fecha, hora, usuario, subtotal, iva, total, 1 if valido else 0))
        factura_id = cur.lastrowid
        for item in items:
            cur.execute("""
                INSERT INTO detalle_factura (factura_id, producto_id, cantidad, subtotal, iva, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (factura_id, item['prod_id'], item['cantidad'], item['subtotal'], item['iva'], item['total']))
        self.conn.commit()

    def obtener_facturas_validas(self) -> List[Tuple[int, str, str, str, str, float, float, float]]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, nit, fecha, hora, usuario, subtotal, iva, total
            FROM factura WHERE valido = 1 ORDER BY fecha DESC, hora DESC
        """)
        return cur.fetchall()

    def eliminar_factura(self, factura_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM detalle_factura WHERE factura_id = ?", (factura_id,))
        cur.execute("DELETE FROM factura WHERE id = ?", (factura_id,))
        self.conn.commit()

    def generar_reporte_csv(self, valido: Optional[bool] = None, filename: str = "reporte_facturas.csv"):
        cur = self.conn.cursor()
        query = """
            SELECT f.id, c.nombre, f.nit, f.fecha, f.hora, f.usuario, f.subtotal, f.iva, f.total
            FROM factura f JOIN cliente c ON f.nit = c.nit
        """
        params = []
        if valido is not None:
            query += " WHERE f.valido = ?"
            params.append(1 if valido else 0)
        query += " ORDER BY f.fecha DESC, f.hora DESC"
        cur.execute(query, params)
        rows = cur.fetchall()

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Cliente", "NIT", "Fecha", "Hora", "Usuario", "Subtotal COP", "IVA COP", "Total COP"])
            for row in rows:
                writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], f"{row[6]:,.2f}", f"{row[7]:,.2f}", f"{row[8]:,.2f}"])
        return filename


# ====================== INTERFAZ GRÁFICA ======================
class AppFacturacion:
    def __init__(self):
        self.db = GestorDB()
        self.root = tk.Tk()
        self.root.title("Facturación PRO - Electrónica General")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.carrito: List[Dict] = []
        self.current_user = None
        self.running = True  # valida las animaciones
        self._setup_animations()
        self._setup_closing()
        self._mostrar_login()

    def _setup_animations(self):
        self.root.option_add("*Font", "Helvetica 10")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Accent.TButton", foreground="white", background="#0078D7")
        style.map("Accent.TButton", background=[("active", "#005BB5")])

    def _animate_text(self, widget, start_alpha=0, end_alpha=1, steps=10, delay=50):
        if not self.running or not hasattr(widget, "_alpha"):
            return
        widget._alpha = start_alpha if not hasattr(widget, "_alpha") else widget._alpha
        if widget._alpha < end_alpha:
            widget._alpha += (end_alpha - start_alpha) / steps
            color = f'#{"%02x" % int(255 * widget._alpha)}{"%02x" % int(255 * widget._alpha)}{"%02x" % int(255 * widget._alpha)}'
            widget.configure(background=color, foreground="black" if widget._alpha >= 1 else "gray")
            self.root.after(delay, lambda: self._animate_text(widget, start_alpha, end_alpha, steps, delay))

    def _animate_button_hover(self, button):
        def on_enter(e):
            if self.running:
                button.configure(style="Accent.TButton")
                bg = tk.StringVar(value="#005BB5")
                button.configure(background=bg.get())
                self.root.after(100, lambda: button.configure(background=bg.get()) if button.winfo_exists() else None)

        def on_leave(e):
            if self.running:
                button.configure(style="Accent.TButton")
                bg = tk.StringVar(value="#0078D7")
                button.configure(background=bg.get())
                self.root.after(100, lambda: button.configure(background=bg.get()) if button.winfo_exists() else None)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def _animate_tab_transition(self, notebook):
        def on_tab_change(event):
            if not self.running:
                return
            frame = notebook.nametowidget(notebook.select())
            # Animar fade-in solo en la pestaña seleccionada
            for child in frame.winfo_children():
                if isinstance(child, ttk.Label) and "text" in child.config():
                    child.configure(background="#FFFFFF")
                    self._animate_text(child, start_alpha=0, end_alpha=1)

        notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    def _setup_closing(self):
        def on_closing():
            self.running = False
            if hasattr(self, 'db') and hasattr(self.db, 'conn'):
                self.db.conn.close()
            self.root.quit()  # Usa quit en lugar de destroy para evitar errores
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

    def _get_saludo(self):
        hora = datetime.now().hour
        if hora < 12:
            return "Buenos días"
        elif hora < 18:
            return "Buenas tardes"
        else:
            return "Buenas noches"

    # --- Login ---
    def _mostrar_login(self):
        login_window = Toplevel(self.root)
        login_window.title("Login Admin")
        login_window.geometry("400x400")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()

        frame = ttk.Frame(login_window, padding=20)
        frame.pack(expand=True, fill="both")
        label_title = ttk.Label(frame, text="LOGIN ADMIN", font=("Helvetica", 16, "bold"))
        label_title.pack(pady=10)
        self._animate_text(label_title)

        # Login
        login_frame = ttk.LabelFrame(frame, text="Iniciar Sesión", padding=10)
        login_frame.pack(fill="x", pady=5)
        ttk.Label(login_frame, text="Usuario:").grid(row=0, column=0, sticky="e")
        self.entry_user = ttk.Entry(login_frame)
        self.entry_user.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(login_frame, text="Contraseña:").grid(row=1, column=0, sticky="e")
        self.entry_pass = ttk.Entry(login_frame, show="*")
        self.entry_pass.grid(row=1, column=1, padx=5, pady=5)
        btn_login = ttk.Button(login_frame, text="Ingresar", command=lambda: self._intentar_login(login_window), style="Accent.TButton")
        btn_login.grid(row=2, column=0, columnspan=2, pady=10)
        self._animate_button_hover(btn_login)

        # Registro Admin
        reg_frame = ttk.LabelFrame(frame, text="Registrar Admin", padding=10)
        reg_frame.pack(fill="x", pady=5)
        ttk.Label(reg_frame, text="Usuario:").grid(row=0, column=0, sticky="e")
        self.entry_new_user = ttk.Entry(reg_frame)
        self.entry_new_user.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(reg_frame, text="Contraseña:").grid(row=1, column=0, sticky="e")
        self.entry_new_pass = ttk.Entry(reg_frame, show="*")
        self.entry_new_pass.grid(row=1, column=1, padx=5, pady=5)
        btn_reg = ttk.Button(reg_frame, text="Crear Admin", command=self._registrar_admin, style="Accent.TButton")
        btn_reg.grid(row=2, column=0, columnspan=2, pady=5)
        self._animate_button_hover(btn_reg)

        # Restablecer Contraseña
        reset_frame = ttk.LabelFrame(frame, text="Restablecer Contraseña", padding=10)
        reset_frame.pack(fill="x", pady=5)
        ttk.Label(reset_frame, text="Usuario:").grid(row=0, column=0, sticky="e")
        self.entry_reset_user = ttk.Entry(reset_frame)
        self.entry_reset_user.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(reset_frame, text="Nueva Contraseña:").grid(row=1, column=0, sticky="e")
        self.entry_reset_pass = ttk.Entry(reset_frame, show="*")
        self.entry_reset_pass.grid(row=1, column=1, padx=5, pady=5)
        btn_reset = ttk.Button(reset_frame, text="Restablecer", command=self._reset_password, style="Accent.TButton")
        btn_reset.grid(row=2, column=0, columnspan=2, pady=5)
        self._animate_button_hover(btn_reset)

    def _intentar_login(self, window):
        usuario, pwd = self.entry_user.get().strip(), self.entry_pass.get().strip()
        if not (usuario and pwd):
            messagebox.showwarning("Error", "Complete los campos")
            return
        if self.db.login(usuario, pwd):
            self.current_user = usuario
            window.destroy()
            self._mostrar_principal()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")

    def _registrar_admin(self):
        usuario, pwd = self.entry_new_user.get().strip(), self.entry_new_pass.get().strip()
        if not (AutomataValidador.usuario(usuario) and len(pwd) >= 6):
            messagebox.showwarning("Error", "Usuario (4-20 caracteres alfanuméricos) y contraseña (mín. 6 caracteres)")
            return
        if self.db.agregar_admin(usuario, pwd):
            messagebox.showinfo("Éxito", f"Admin '{usuario}' creado")
            self.entry_new_user.delete(0, tk.END)
            self.entry_new_pass.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Usuario ya existe")

    def _reset_password(self):
        usuario, new_pwd = self.entry_reset_user.get().strip(), self.entry_reset_pass.get().strip()
        if not (AutomataValidador.usuario(usuario) and len(new_pwd) >= 6):
            messagebox.showwarning("Error", "Usuario inválido o contraseña menor a 6 caracteres")
            return
        if self.db.reset_password(usuario, new_pwd):
            messagebox.showinfo("Éxito", f"Contraseña de '{usuario}' restablecida")
            self.entry_reset_user.delete(0, tk.END)
            self.entry_reset_pass.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Usuario no existe")

    # --- ventana principal ---
    def _mostrar_principal(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self._animate_tab_transition(notebook)

        tab_fact = ttk.Frame(notebook)
        tab_prod = ttk.Frame(notebook)
        tab_rep = ttk.Frame(notebook)
        notebook.add(tab_fact, text="Facturar")
        notebook.add(tab_prod, text="Productos")
        notebook.add(tab_rep, text="Reportes")

        self._construir_facturar(tab_fact)
        self._construir_productos(tab_prod)
        self._construir_reportes(tab_rep)

    # --- Facturar ---
    def _construir_facturar(self, parent):
        # Saludo dinámico
        frame_saludo = ttk.Frame(parent)
        frame_saludo.pack(anchor="nw", padx=10, pady=5)
        saludo = f"{self._get_saludo()}, {self.current_user}"
        label_saludo = ttk.Label(frame_saludo, text=saludo, font=("Helvetica", 12, "bold"))
        label_saludo.pack(side="left")
        self._animate_text(label_saludo)

        # Cliente
        frame_cli = ttk.LabelFrame(parent, text="Cliente", padding=10)
        frame_cli.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame_cli, text="NIT:").grid(row=0, column=0)
        self.entry_nit = ttk.Entry(frame_cli, width=20)
        self.entry_nit.grid(row=0, column=1, padx=5)
        ttk.Label(frame_cli, text="Nombre:").grid(row=0, column=2)
        self.entry_nombre = ttk.Entry(frame_cli, width=30)
        self.entry_nombre.grid(row=0, column=3, padx=5)
        btn_reg = ttk.Button(frame_cli, text="Registrar", command=self._reg_cliente, style="Accent.TButton")
        btn_reg.grid(row=0, column=4)
        self._animate_button_hover(btn_reg)

        # Fecha
        frame_fecha = ttk.LabelFrame(parent, text="Fecha", padding=10)
        frame_fecha.pack(fill="x", padx=10, pady=5)
        self.cal = Calendar(frame_fecha, date_pattern="yyyy-mm-dd")
        self.cal.pack()

        # Productos
        frame_prod = ttk.LabelFrame(parent, text="Productos Disponibles", padding=10)
        frame_prod.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        cols = ("ID", "Producto", "Precio", "Cat")
        self.tree_prod = ttk.Treeview(frame_prod, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree_prod.heading(col, text=col)
            self.tree_prod.column(col, width=80 if col != "Producto" else 220, anchor="center")
        self.tree_prod.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame_prod, command=self.tree_prod.yview)
        sb.pack(side="right", fill="y")
        self.tree_prod.configure(yscrollcommand=sb.set)

        # Cantidad y Agregar
        frame_ctrl = ttk.Frame(frame_prod)
        frame_ctrl.pack(fill="x", pady=5)
        ttk.Label(frame_ctrl, text="Cantidad:").pack(side="left")
        self.spin_cant = ttk.Spinbox(frame_ctrl, from_=1, to=100, width=5)
        self.spin_cant.pack(side="left", padx=5)
        self.spin_cant.insert(0, "1")
        btn_add = ttk.Button(frame_ctrl, text="Agregar al Carrito", command=self._add_carrito, style="Accent.TButton")
        btn_add.pack(side="left", padx=5)
        self._animate_button_hover(btn_add)

        # Carrito
        frame_car = ttk.LabelFrame(parent, text="Carrito", padding=10)
        frame_car.pack(side="right", fill="both", expand=True, padx=10, pady=5)
        cols_car = ("Prod", "Cant", "Subtotal", "IVA", "Total")
        self.tree_car = ttk.Treeview(frame_car, columns=cols_car, show="headings", height=10)
        for col in cols_car:
            self.tree_car.heading(col, text=col)
            self.tree_car.column(col, width=80, anchor="center")
        self.tree_car.pack(side="left", fill="both", expand=True)
        sb_car = ttk.Scrollbar(frame_car, command=self.tree_car.yview)
        sb_car.pack(side="right", fill="y")
        self.tree_car.configure(yscrollcommand=sb_car.set)
        btn_del = ttk.Button(frame_car, text="Quitar", command=self._del_carrito, style="Accent.TButton")
        btn_del.pack(pady=5)
        self._animate_button_hover(btn_del)

        # Total
        frame_total = ttk.LabelFrame(parent, text="Resumen", padding=10)
        frame_total.pack(fill="x", padx=10, pady=5)
        self.lbl_subtotal = ttk.Label(frame_total, text="Subtotal: $0.00 COP", width=30, anchor="e")
        self.lbl_subtotal.pack(side="left", padx=10)
        self._animate_text(self.lbl_subtotal)
        self.lbl_iva = ttk.Label(frame_total, text="IVA (19%): $0.00 COP", width=30, anchor="e")
        self.lbl_iva.pack(side="left", padx=10)
        self._animate_text(self.lbl_iva)
        self.lbl_total = ttk.Label(frame_total, text="Total: $0.00 COP", font=("Helvetica", 14, "bold"), width=30, anchor="e")
        self.lbl_total.pack(side="left", padx=10)
        self._animate_text(self.lbl_total)

        # Botón Realizar Importe fijo en la parte inferior
        frame_bottom = ttk.Frame(parent)
        frame_bottom.pack(fill="x", side="bottom", anchor="s", pady=10)
        btn_importe = ttk.Button(frame_bottom, text="Realizar Importe", style="Accent.TButton", command=self._gen_factura)
        btn_importe.pack(side="right", padx=10)
        self._animate_button_hover(btn_importe)

        self._cargar_productos()

    def _cargar_productos(self, cat_id: Optional[int] = None):
        for i in self.tree_prod.get_children():
            self.tree_prod.delete(i)
        for prod in self.db.listar_productos(cat_id):
            self.tree_prod.insert("", "end", values=prod)

    def _reg_cliente(self):
        nit, nombre = self.entry_nit.get().strip(), self.entry_nombre.get().strip()
        if not (nit and nombre and AutomataValidador.nit(nit)):
            messagebox.showwarning("Error", "NIT inválido o campos vacíos")
            return
        if self.db.registrar_cliente(nit, nombre):
            messagebox.showinfo("Éxito", "Cliente registrado")
        else:
            messagebox.showerror("Error", "NIT ya existe")

    def _add_carrito(self):
        sel = self.tree_prod.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione un producto")
            return
        item = self.tree_prod.item(sel[0])["values"]
        if not item or len(item) < 3:
            messagebox.showwarning("Error", "Producto no válido")
            return
        prod_id, nombre, precio, _ = item
        try:
            cant = int(self.spin_cant.get())
        except ValueError:
            messagebox.showwarning("Error", "Cantidad debe ser un número válido")
            return
        if cant < 1:
            messagebox.showwarning("Error", "Cantidad debe ser mayor a 0")
            return
        subtotal = float(precio) * cant
        iva = subtotal * self.db.IVA_RATE
        total = subtotal + iva
        for i in self.tree_car.get_children():
            if self.tree_car.item(i)["values"][0] == nombre:
                messagebox.showinfo("Duplicado", "Producto ya en carrito")
                return
        self.carrito.append({"prod_id": prod_id, "nombre": nombre, "precio": float(precio), "cantidad": cant,
                             "subtotal": subtotal, "iva": iva, "total": total})
        self.tree_car.insert("", "end", values=(nombre, cant, f"{subtotal:,.2f}", f"{iva:,.2f}", f"{total:,.2f}"))
        self._actualizar_total()

    def _del_carrito(self):
        sel = self.tree_car.selection()
        if not sel:
            return
        idx = self.tree_car.index(sel[0])
        self.carrito.pop(idx)
        self.tree_car.delete(sel[0])
        self._actualizar_total()

    def _actualizar_total(self):
        subtotal = sum(i["subtotal"] for i in self.carrito)
        iva = sum(i["iva"] for i in self.carrito)
        total = sum(i["total"] for i in self.carrito)
        self.lbl_subtotal.config(text=f"Subtotal: ${subtotal:,.2f} COP")
        self.lbl_iva.config(text=f"IVA (19%): ${iva:,.2f} COP")
        self.lbl_total.config(text=f"Total: ${total:,.2f} COP")

    def _gen_factura(self):
        nit, fecha = self.entry_nit.get().strip(), self.cal.get_date()
        if not (nit and self.carrito and AutomataValidador.nit(nit) and AutomataValidador.fecha(fecha)):
            messagebox.showwarning("Faltan datos", "Verifique NIT, fecha y productos")
            return
        subtotal = sum(i["subtotal"] for i in self.carrito)
        iva = sum(i["iva"] for i in self.carrito)
        total = sum(i["total"] for i in self.carrito)
        valido = total > 0
        items_db = [{"prod_id": i["prod_id"], "cantidad": i["cantidad"], "subtotal": i["subtotal"],
                     "iva": i["iva"], "total": i["total"]} for i in self.carrito]
        hora = datetime.now().strftime("%H:%M:%S")
        self.db.guardar_factura(nit, fecha, hora, self.current_user, items_db, subtotal, iva, total, valido)

        cliente = self.db.conn.execute("SELECT nombre FROM cliente WHERE nit = ?", (nit,)).fetchone()
        cliente = cliente[0] if cliente else "Desconocido"
        recibo = f"""=== FACTURA ELECTRÓNICA ===
Cliente: {cliente}
NIT: {nit}
Fecha: {fecha}
Hora: {hora}
Usuario: {self.current_user}
{'='*70}
{'Producto':<25} {'Cant':>6} {'Subtotal':>12} {'IVA':>12} {'Total':>12}
{'-'*70}"""
        for i in self.carrito:
            recibo += f"\n{i['nombre']:<25} {i['cantidad']:>6} {i['subtotal']:>12,.2f} {i['iva']:>12,.2f} {i['total']:>12,.2f}"
        recibo += f"\n{'-'*70}\nSubtotal: {subtotal:>45,.2f} COP\nIVA (19%): {iva:>44,.2f} COP\nTOTAL: {total:>47,.2f} COP"
        recibo += f"\n\nEstado: {'VÁLIDA' if valido else 'INVÁLIDA'}"
        messagebox.showinfo("Factura Generada", recibo)

        self.entry_nit.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.carrito.clear()
        for i in self.tree_car.get_children():
            self.tree_car.delete(i)
        self._actualizar_total()
        self._cargar_reportes()

    # --- Productos ---
    def _construir_productos(self, parent):
        frame = ttk.LabelFrame(parent, text="Gestión de Productos", padding=15)
        frame.pack(fill="both", expand=True)
        sub = ttk.Frame(frame)
        sub.pack(fill="x", pady=5)
        ttk.Label(sub, text="Nombre:").pack(side="left")
        self.e_nom = ttk.Entry(sub, width=30)
        self.e_nom.pack(side="left", padx=5)
        ttk.Label(sub, text="Precio:").pack(side="left")
        self.e_pre = ttk.Entry(sub, width=15)
        self.e_pre.pack(side="left", padx=5)
        ttk.Label(sub, text="Categoría:").pack(side="left")
        self.combo_cat_prod = ttk.Combobox(sub, state="readonly", width=20)
        self.combo_cat_prod.pack(side="left", padx=5)
        btn_add = ttk.Button(sub, text="Agregar", command=self._add_prod, style="Accent.TButton")
        btn_add.pack(side="left", padx=5)
        self._animate_button_hover(btn_add)

        cols = ("ID", "Producto", "Precio", "Categoría")
        self.tree_gest = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree_gest.heading(col, text=col)
            self.tree_gest.column(col, width=80 if col != "Producto" else 250)
        self.tree_gest.pack(fill="both", expand=True, pady=5)
        self._cargar_categorias_gestion()
        self._cargar_productos_gestion()

    def _cargar_categorias_gestion(self):
        cats = self.db.listar_categorias()
        self.combo_cat_prod['values'] = [c[1] for c in cats]
        if cats:
            self.combo_cat_prod.current(0)

    def _add_prod(self):
        nombre, precio = self.e_nom.get().strip(), self.e_pre.get().strip()
        try:
            precio = float(precio)
        except:
            messagebox.showerror("Error", "Precio inválido")
            return
        cat_nombre = self.combo_cat_prod.get()
        if not (nombre and precio > 0 and cat_nombre):
            messagebox.showwarning("Faltan datos", "Complete nombre, precio y categoría")
            return
        cat_id = self.db.conn.execute("SELECT id FROM categoria WHERE nombre = ?", (cat_nombre,)).fetchone()[0]
        if self.db.agregar_producto(nombre, precio, cat_id):
            messagebox.showinfo("Éxito", "Producto agregado")
            self.e_nom.delete(0, tk.END)
            self.e_pre.delete(0, tk.END)
            self._cargar_productos_gestion()
            self._cargar_productos()
        else:
            messagebox.showerror("Error", "Producto ya existe")

    def _cargar_productos_gestion(self):
        for i in self.tree_gest.get_children():
            self.tree_gest.delete(i)
        for p in self.db.listar_productos():
            self.tree_gest.insert("", "end", values=p)

    # --- Reportes ---
    def _construir_reportes(self, parent):
        frame = ttk.LabelFrame(parent, text="Gestión de Reportes", padding=20)
        frame.pack(fill="both", expand=True)
        label_title = ttk.Label(frame, text="Gestión de Reportes", font=("Helvetica", 12, "bold"))
        label_title.pack(pady=5)
        self._animate_text(label_title)

        # Lista de facturas válidas
        self.tree_rep = ttk.Treeview(frame, columns=("ID", "Fecha", "Hora", "Usuario", "NIT", "Total"), show="headings", height=10)
        for col in ("ID", "Fecha", "Hora", "Usuario", "NIT", "Total"):
            self.tree_rep.heading(col, text=col)
            self.tree_rep.column(col, width=100 if col != "Total" else 120, anchor="center")
        self.tree_rep.pack(fill="both", expand=True, pady=5)
        sb_rep = ttk.Scrollbar(frame, command=self.tree_rep.yview)
        sb_rep.pack(side="right", fill="y")
        self.tree_rep.configure(yscrollcommand=sb_rep.set)

        # Botones de acción
        frame_btn = ttk.Frame(frame)
        frame_btn.pack(fill="x", pady=10)
        btn_ver = ttk.Button(frame_btn, text="Ver en Interfaz", command=self._mostrar_reportes, style="Accent.TButton")
        btn_ver.pack(side="left", padx=5)
        self._animate_button_hover(btn_ver)
        btn_exp = ttk.Button(frame_btn, text="Exportar a TXT", command=self._exportar_txt, style="Accent.TButton")
        btn_exp.pack(side="left", padx=5)
        self._animate_button_hover(btn_exp)
        btn_del = ttk.Button(frame_btn, text="Eliminar del Registro", command=self._eliminar_factura, style="Accent.TButton")
        btn_del.pack(side="left", padx=5)
        self._animate_button_hover(btn_del)

        self._cargar_reportes()

    def _cargar_reportes(self):
        for i in self.tree_rep.get_children():
            self.tree_rep.delete(i)
        facturas = self.db.obtener_facturas_validas()
        for f in facturas:
            self.tree_rep.insert("", "end", values=(f[0], f[2], f[3], f[4], f[1], f"{f[7]:,.2f} COP"))

    def _mostrar_reportes(self):
        sel = self.tree_rep.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione una factura")
            return
        factura_id = self.tree_rep.item(sel[0])["values"][0]
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT f.nit, f.fecha, f.hora, f.usuario, f.subtotal, f.iva, f.total, c.nombre
            FROM factura f JOIN cliente c ON f.nit = c.nit WHERE f.id = ?
        """, (factura_id,))
        f = cur.fetchone()
        if not f:
            messagebox.showerror("Error", f"No se encontraron datos para la factura ID {factura_id}")
            return
        cur.execute("SELECT p.nombre, d.cantidad, d.subtotal, d.iva, d.total FROM detalle_factura d JOIN producto p ON d.producto_id = p.id WHERE d.factura_id = ?", (factura_id,))
        detalles = cur.fetchall()
        recibo = f"""=== FACTURA ELECTRÓNICA ===
Cliente: {f[7]}
NIT: {f[0]}
Fecha: {f[1]}
Hora: {f[2]}
Usuario: {f[3]}
{'='*70}
{'Producto':<25} {'Cant':>6} {'Subtotal':>12} {'IVA':>12} {'Total':>12}
{'-'*70}"""
        for d in detalles:
            recibo += f"\n{d[0]:<25} {d[1]:>6} {d[2]:>12,.2f} {d[3]:>12,.2f} {d[4]:>12,.2f}"
        recibo += f"\n{'-'*70}\nSubtotal: {f[4]:>45,.2f} COP\nIVA (19%): {f[5]:>44,.2f} COP\nTOTAL: {f[6]:>47,.2f} COP"
        recibo += f"\n\nEstado: VÁLIDA"
        messagebox.showinfo("Detalles de Factura", recibo)

    def _exportar_txt(self):
        sel = self.tree_rep.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione una factura")
            return
        factura_id = self.tree_rep.item(sel[0])["values"][0]
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT f.nit, f.fecha, f.hora, f.usuario, f.subtotal, f.iva, f.total, c.nombre
            FROM factura f JOIN cliente c ON f.nit = c.nit WHERE f.id = ?
        """, (factura_id,))
        f = cur.fetchone()
        if not f:
            messagebox.showerror("Error", f"No se encontraron datos para la factura ID {factura_id}")
            return
        cur.execute("SELECT p.nombre, d.cantidad, d.subtotal, d.iva, d.total FROM detalle_factura d JOIN producto p ON d.producto_id = p.id WHERE d.factura_id = ?", (factura_id,))
        detalles = cur.fetchall()
        recibo = f"""=== FACTURA ELECTRÓNICA ===
Cliente: {f[7]}
NIT: {f[0]}
Fecha: {f[1]}
Hora: {f[2]}
Usuario: {f[3]}
{'='*70}
{'Producto':<25} {'Cant':>6} {'Subtotal':>12} {'IVA':>12} {'Total':>12}
{'-'*70}"""
        for d in detalles:
            recibo += f"\n{d[0]:<25} {d[1]:>6} {d[2]:>12,.2f} {d[3]:>12,.2f} {d[4]:>12,.2f}"
        recibo += f"\n{'-'*70}\nSubtotal: {f[4]:>45,.2f} COP\nIVA (19%): {f[5]:>44,.2f} COP\nTOTAL: {f[6]:>47,.2f} COP"
        recibo += f"\n\nEstado: VÁLIDA"
        with open(f"factura_{factura_id}.txt", "w", encoding="utf-8") as f:
            f.write(recibo)
        messagebox.showinfo("Éxito", f"Factura exportada como factura_{factura_id}.txt")

    def _eliminar_factura(self):
        sel = self.tree_rep.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione una factura")
            return
        factura_id = self.tree_rep.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar factura ID {factura_id}?"):
            self.db.eliminar_factura(factura_id)
            self._cargar_reportes()
            messagebox.showinfo("Éxito", f"Factura ID {factura_id} eliminada")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AppFacturacion()
    app.run()