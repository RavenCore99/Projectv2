import sqlite3
import csv
from datetime import datetime
from typing import List, Dict, Tuple, Optional

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
        from validador import AutomataValidador
        if not (AutomataValidador.usuario(usuario) and len(password) >= 6):
            return False
        try:
            self.conn.execute("INSERT INTO admin (usuario, password) VALUES (?, ?)", (usuario, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def reset_password(self, usuario: str, new_password: str) -> bool:
        from validador import AutomataValidador
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