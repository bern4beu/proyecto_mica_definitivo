# ESTADO ACTUAL:
# Ventas con detalle funcionando correctamente.
# Stock se descuenta y total se calcula automáticamente.


from flask import Flask, request, render_template_string
import psycopg2
import os

app = Flask(__name__)

@app.route("/test")
def test():
    return "FLASK FUNCIONA"

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(database_url, sslmode="require")


@app.route("/health")
def health():
    return "OK"




# ----------- INICIO ---------------------

HTML_HOME = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Sistema de Gestión</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f6f8;
            padding: 40px;
        }
        h1 {
            margin-bottom: 20px;
        }
        .section {
            background: #ffffff;
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 8px;
            max-width: 520px;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            margin: 10px 0;
        }
        a {
            text-decoration: none;
            color: #0066cc;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<h1>Sistema de Gestión</h1>

<div class="section">
    <h2>Carga de datos</h2>
    <ul>
        <li><a href="/clientes">Clientes</a></li>
        <li><a href="/proveedor">Proveedores</a></li>
        <li><a href="/agregar_vehiculo">Vehículos</a></li>

        <li><a href="/producto_base">Producto base</a></li>
        <li><a href="/producto_variante">Producto variante</a></li>
        <li><a href="/producto_vehiculo">Asociar producto ↔ vehículo</a></li>

        <li><a href="/venta">Registrar venta</a></li>
    </ul>
</div>

<div class="section">
    <h2>Consultas</h2>
    <ul>
        <li><a href="/ventas">📄 Ventas</a></li>
        <li><a href="/productos">📦 Productos</a></li>
        <li><a href="/stock-bajo">⚠️ Stock bajo</a></li>
        <li><a href="/productos-mas-vendidos">🔥 Productos más vendidos</a></li>

    </ul>
</div>

</body>
</html>
'''


@app.route('/')
def home():
    return render_template_string(HTML_HOME)


# ---------- CLIENTES ----------
HTML_FORM_CLIENTE = '''
<h2>Agregar Cliente</h2>
<form method="POST">
  Nombre del cliente: <input type="text" name="nombre" required>
  <input type="submit" value="Agregar">
</form>
<a href="/producto_base">Ir a Producto Base</a><br>
<a href="/agregar_vehiculo">Ir a Vehículos</a>
'''

@app.route('/clientes', methods=['GET', 'POST'])
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']

        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute("INSERT INTO cliente (nombre) VALUES (%s)", (nombre,))
        conn.commit()
        cur.close()
        conn.close()

        return f'Cliente "{nombre}" agregado con éxito!<br><a href="/">Volver</a>'

    return render_template_string(HTML_FORM_CLIENTE)


# ---------- VEHICULOS ----------
HTML_FORM_VEHICULO = '''
<h2>Agregar Vehículo</h2>

<form method="POST">
  Marca: <input type="text" name="marca" required><br><br>
  Modelo: <input type="text" name="modelo" required><br><br>
  Motor: <input type="text" name="motor"><br><br>

  <input type="submit" value="Agregar Vehículo">
</form>

<br>
<a href="/">Volver</a>
'''

@app.route("/agregar_vehiculo", methods=["GET", "POST"])
def agregar_vehiculo():
    if request.method == "POST":
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        motor = request.form["motor"] or None

        conn = get_db_connection()

        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO vehiculo (marca, modelo, motor)
                VALUES (%s, %s, %s)
            """, (marca, modelo, motor))
            conn.commit()

        except Exception as e:
            conn.rollback()
            return f"Error al guardar vehículo: {e}"

        finally:
            cur.close()
            conn.close()

        return 'Vehículo agregado con éxito<br><a href="/agregar_vehiculo">Agregar otro</a>'

    return render_template_string(HTML_FORM_VEHICULO)


# ---------- PRODUCTO BASE ----------
def to_numeric_or_none(value):
    return value if value != '' else None

HTML_FORM_BASE = '''
<h2>Agregar Producto Base</h2>
<form method="POST">
  Nombre: <input type="text" name="nombre"><br>
  Descripción: <input type="text" name="descripcion"><br>
  Alto: <input type="number" name="alto" step="0.01"><br>
  Ancho: <input type="number" name="ancho" step="0.01"><br>
  Largo: <input type="number" name="largo" step="0.01"><br>
  Diámetro: <input type="number" name="diametro" step="0.01"><br>
  <input type="submit" value="Agregar">
</form>
<a href="/">Volver a Clientes</a>
'''

@app.route('/producto_base', methods=['GET', 'POST'])
def agregar_producto_base():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        alto = to_numeric_or_none(request.form['alto'])
        ancho = to_numeric_or_none(request.form['ancho'])
        largo = to_numeric_or_none(request.form['largo'])
        diametro = to_numeric_or_none(request.form['diametro'])

        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO producto_base
            (nombre, descripcion, alto, ancho, largo, diametro)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nombre, descripcion, alto, ancho, largo, diametro))
        conn.commit()
        cur.close()
        conn.close()

        return f'Producto base "{nombre}" agregado con éxito!<br><a href="/producto_base">Agregar otro</a>'

    return render_template_string(HTML_FORM_BASE)


# --------- PRODUCTO BASE ↔ VEHICULO ----------

HTML_FORM_PRODUCTO_VEHICULO = '''
<h2>Asociar Producto Base con Vehículos</h2>

<form method="POST">

Producto Base:
<select name="id_producto_base" required>
  {% for p in productos %}
    <option value="{{ p[0] }}">{{ p[1] }}</option>
  {% endfor %}
</select>

<br><br>

Vehículos (podés seleccionar varios):
<br>
<select name="vehiculos" multiple size="6" required>
  {% for v in vehiculos %}
    <option value="{{ v[0] }}">{{ v[1] }} {{ v[2] }} {{ v[3] or '' }}</option>
  {% endfor %}
</select>

<br><br>

<input type="submit" value="Asociar">
</form>

<br>
<a href="/">Volver</a>
'''

@app.route('/producto_vehiculo', methods=['GET', 'POST'])
def asociar_producto_vehiculo():
    conn = get_db_connection()

    cur = conn.cursor()

    if request.method == 'POST':
        id_producto_base = request.form['id_producto_base']
        ids_vehiculos = request.form.getlist('vehiculos')

        for id_vehiculo in ids_vehiculos:
            cur.execute("""
                INSERT INTO producto_vehiculo (id_producto_base, id_vehiculo)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (id_producto_base, id_vehiculo))

        conn.commit()

        return 'Vehículos asociados correctamente<br><a href="/producto_vehiculo">Asociar otro</a>'

    cur.execute("SELECT id, nombre FROM producto_base ORDER BY nombre")
    productos = cur.fetchall()

    cur.execute("SELECT id, marca, modelo, motor FROM vehiculo ORDER BY marca, modelo")
    vehiculos = cur.fetchall()

     # 🔴 CASOS SIN DATOS
    if not productos:
        return '''
        <h2>No hay productos base cargados</h2>
        <p>Primero tenés que cargar al menos un producto base.</p>
        <a href="/producto_base">Cargar producto base</a><br>
        <a href="/">Volver</a>
        '''

    if not vehiculos:
        return '''
        <h2>No hay vehículos cargados</h2>
        <p>Primero tenés que cargar vehículos.</p>
        <a href="/vehiculos">Cargar vehículos</a><br>
        <a href="/">Volver</a>
        '''

    return render_template_string(
        HTML_FORM_PRODUCTO_VEHICULO,
        productos=productos,
        vehiculos=vehiculos
    )



# ---------- PROVEEDORES ----------
HTML_FORM_PROVEEDOR = '''
<h2>Agregar Proveedor</h2>
<form method="POST">
  Nombre del proveedor: <input type="text" name="nombre" required><br><br>
  <input type="submit" value="Agregar Proveedor">
</form>

<br>
<a href="/producto_variante">Ir a Producto Variante</a><br>
<a href="/">Volver a Clientes</a>
'''

@app.route('/proveedor', methods=['GET', 'POST'])
def agregar_proveedor():
    if request.method == 'POST':
        nombre = request.form['nombre']

        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO proveedor (nombre) VALUES (%s)",
            (nombre,)
        )
        conn.commit()
        cur.close()
        conn.close()

        return f'Proveedor "{nombre}" agregado con éxito<br><a href="/proveedor">Agregar otro</a>'

    return render_template_string(HTML_FORM_PROVEEDOR)


# ---------- PRODUCTO VARIANTE ----------
HTML_FORM_VARIANTE = '''
<h2>Agregar Producto Variante</h2>
<form method="POST">

Producto Base:
<select name="id_producto_base" required>
  {% for p in productos %}
    <option value="{{ p[0] }}">{{ p[1] }}</option>
  {% endfor %}
</select>
<br><br>

Marca: <input type="text" name="marca" required><br><br>

Calidad: <input type="text" name="calidad"><br><br>

Precio venta: <input type="number" step="0.01" name="precio" required><br><br>

Precio compra: <input type="number" step="0.01" name="precio_compra"><br><br>

Stock: <input type="number" name="stock" required><br><br>

Ubicación: <input type="text" name="ubicacion"><br><br>

Proveedor:
<select name="id_proveedor">
  <option value="">-- Sin proveedor --</option>
  {% for prov in proveedores %}
    <option value="{{ prov[0] }}">{{ prov[1] }}</option>
  {% endfor %}
</select>
<br><br>

<input type="submit" value="Agregar Variante">
</form>
'''

from psycopg2 import errors

@app.route('/producto_variante', methods=['GET', 'POST'])
def agregar_producto_variante():
    conn = get_db_connection()
    
    cur = conn.cursor()

    if request.method == 'POST':
        try:
            cur.execute("""
                INSERT INTO producto_variante
                (id_producto_base, marca, calidad, precio, precio_compra, stock, ubicacion, id_proveedor)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                request.form['id_producto_base'],
                request.form['marca'],
                request.form['calidad'],
                request.form['precio'],
                request.form['precio_compra'] or None,
                request.form['stock'],
                request.form['ubicacion'],
                request.form['id_proveedor'] or None
            ))
            conn.commit()
            mensaje = 'Producto variante agregado con éxito<br><a href="/producto_variante">Agregar otro</a>'
        except errors.UniqueViolation:
            conn.rollback()
            mensaje = 'Error: ya existe un producto variante con ese Producto Base y Marca.'
        finally:
            cur.close()
            conn.close()

        return mensaje

    # GET
    cur.execute("""
        SELECT id,
            nombre,
            alto,
            ancho,
            largo,
            diametro
        FROM producto_base
        ORDER BY nombre
    """)
    productos = cur.fetchall()

     # 🔴 SI NO HAY PRODUCTOS BASE
    if not productos:
        cur.close()
        conn.close()
        return '''
        <h2>No hay productos base cargados</h2>
        <p>Primero tenés que crear un producto base.</p>
        <a href="/producto_base">Cargar producto base</a><br>
        <a href="/">Volver</a>
        '''

    # Construimos la lista que se va a mostrar en el select
    productos_para_select = []
    for p in productos:
        id_prod = p[0]
        nombre = p[1]
        alto, ancho, largo, diametro = p[2], p[3], p[4], p[5]

        if alto or ancho or largo or diametro:
            display = f"{nombre} ({alto or ''}x{ancho or ''}x{largo or ''}x{diametro or ''})"
        else:
            display = nombre

        productos_para_select.append((id_prod, display))



    cur.execute("SELECT id, nombre FROM proveedor ORDER BY nombre")
    proveedores = cur.fetchall()
    cur.close()
    conn.close()

    return render_template_string(
        HTML_FORM_VARIANTE,
        productos=productos_para_select,
        proveedores=proveedores
    )


# ------------------ VENTA ------------------------------

HTML_FORM_VENTA = '''
<h2>Registrar Venta</h2>

<form method="POST">

Cliente:
<select name="id_cliente">
  <option value="">-- Sin cliente --</option>  
  {% for c in clientes %}
    <option value="{{ c[0] }}">{{ c[1] }}</option>
  {% endfor %}
</select>

<hr>

<h4>Producto 1</h4>
<select name="producto_1">
  <option value="">-- Seleccionar --</option>
  {% for p in productos %}
    <option value="{{ p[0] }}">{{ p[1] }}</option>
  {% endfor %}
</select>
Cantidad: <input type="number" name="cantidad_1" min="1">

<h4>Producto 2</h4>
<select name="producto_2">
  <option value="">-- Seleccionar --</option>
  {% for p in productos %}
    <option value="{{ p[0] }}">{{ p[1] }}</option>
  {% endfor %}
</select>
Cantidad: <input type="number" name="cantidad_2" min="1">

<h4>Producto 3</h4>
<select name="producto_3">
  <option value="">-- Seleccionar --</option>
  {% for p in productos %}
    <option value="{{ p[0] }}">{{ p[1] }}</option>
  {% endfor %}
</select>
Cantidad: <input type="number" name="cantidad_3" min="1">

<br><br>
<input type="submit" value="Guardar Venta">
</form>
'''


@app.route('/venta', methods=['GET', 'POST'])
def agregar_venta():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        id_cliente = request.form['id_cliente'] or None

        cur.execute(
            "INSERT INTO venta (id_cliente, total) VALUES (%s, 0) RETURNING id",
            (id_cliente,)
        )
        id_venta = cur.fetchone()[0]

        total = 0
        hay_productos = False

        for i in [1, 2, 3]:
            producto = request.form.get(f'producto_{i}')
            cantidad = request.form.get(f'cantidad_{i}')

            if producto and cantidad:
                cur.execute(
                    "SELECT precio FROM producto_variante WHERE id = %s",
                    (producto,)
                )
                row = cur.fetchone()

                if not row:
                    continue  # producto inválido, lo salteamos

                precio_unitario = row[0]

                cur.execute("""
                    INSERT INTO venta_detalle
                    (id_venta, id_producto_variante, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (id_venta, producto, cantidad, precio_unitario))

                total += precio_unitario * int(cantidad)
                hay_productos = True

        if not hay_productos:
            conn.rollback()
            cur.close()
            conn.close()
            return '''
            <h3>No se puede registrar una venta sin productos</h3>
            <a href="/venta">Volver</a>
            '''

        cur.execute(
            "UPDATE venta SET total = %s WHERE id = %s",
            (total, id_venta)
        )

        conn.commit()
        cur.close()
        conn.close()

        return f"Venta registrada correctamente. Total: ${total}"

    # -------- GET --------

    cur.execute("SELECT id, nombre FROM cliente ORDER BY nombre")
    clientes = cur.fetchall()

    cur.execute("""
        SELECT pv.id, pb.nombre || ' - ' || pv.marca
        FROM producto_variante pv
        JOIN producto_base pb ON pb.id = pv.id_producto_base
        ORDER BY pb.nombre
    """)
    productos = cur.fetchall()

    if not productos:
        cur.close()
        conn.close()
        return '''
        <h2>No hay productos para vender</h2>
        <p>Primero cargá productos y sus variantes.</p>
        <a href="/producto_base">Cargar producto base</a><br>
        <a href="/producto_variante">Cargar producto variante</a><br>
        <a href="/">Volver</a>
        '''

    cur.close()
    conn.close()

    return render_template_string(
        HTML_FORM_VENTA,
        clientes=clientes,
        productos=productos
    )



# ----------------- LISTADO VENTA ------------------

HTML_LISTADO_VENTAS = '''
<h2>Ventas</h2>

{% if ventas %}
<table border="1" cellpadding="5">
<tr>
  <th>ID</th>
  <th>Fecha</th>
  <th>Cliente</th>
  <th>Total</th>
  <th>Acciones</th>
</tr>

{% for v in ventas %}
<tr>
  <td>{{ v.id }}</td>
  <td>{{ v.fecha }}</td>
  <td>{{ v.cliente }}</td>
  <td>${{ v.total }}</td>
  <td><a href="/venta/{{ v.id }}">Ver detalle</a></td>
</tr>
{% endfor %}
</table>
{% else %}
<p>No hay ventas registradas.</p>
<a href="/venta">Registrar una venta</a>
{% endif %}

<br><br>
<a href="/">Volver al inicio</a>
'''



@app.route('/ventas')
def listar_ventas_app():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.id,
            v.fecha,
            COALESCE(c.nombre, 'Mostrador') AS cliente,
            v.total
        FROM venta v
        LEFT JOIN cliente c ON c.id = v.id_cliente
        ORDER BY v.fecha DESC
    """)

    ventas = []
    for r in cur.fetchall():
        ventas.append({
            "id": r[0],
            "fecha": r[1].strftime("%d/%m/%Y %H:%M"),
            "cliente": r[2],
            "total": r[3]
        })

    cur.close()
    conn.close()

    return render_template_string(
        HTML_LISTADO_VENTAS,
        ventas=ventas
    )


# ------------------- DETALLE VENTA ---------------------


HTML_DETALLE_VENTA = '''
<h2>Detalle de Venta #{{ venta.id }}</h2>

<p>
<b>Fecha:</b> {{ venta.fecha }}<br>
<b>Cliente:</b> {{ venta.cliente }}<br>
<b>Total:</b> ${{ venta.total }}
</p>

<hr>

<table border="1" cellpadding="5">
<tr>
  <th>Producto</th>
  <th>Cantidad</th>
  <th>Precio unitario</th>
  <th>Subtotal</th>
</tr>

{% for d in detalles %}
<tr>
  <td>{{ d.producto }}</td>
  <td>{{ d.cantidad }}</td>
  <td>${{ d.precio_unitario }}</td>
  <td>${{ d.subtotal }}</td>
</tr>
{% endfor %}
</table>

<br>
<a href="/ventas">Volver a ventas</a>
'''

@app.route('/venta/<int:id_venta>')
def ver_detalle_venta(id_venta):
    conn = get_db_connection()

    cur = conn.cursor()

    # Cabecera de la venta
    cur.execute("""
        SELECT
            v.id,
            v.fecha,
            COALESCE(c.nombre, 'Mostrador') AS cliente,
            v.total
        FROM venta v
        LEFT JOIN cliente c ON c.id = v.id_cliente
        WHERE v.id = %s
    """, (id_venta,))

    v = cur.fetchone()

    venta = {
        "id": v[0],
        "fecha": v[1],
        "cliente": v[2],
        "total": v[3]
    }

    # Detalle de la venta
    cur.execute("""
        SELECT
            pb.nombre || ' - ' || pv.marca AS producto,
            vd.cantidad,
            vd.precio_unitario,
            vd.cantidad * vd.precio_unitario AS subtotal
        FROM venta_detalle vd
        JOIN producto_variante pv ON pv.id = vd.id_producto_variante
        JOIN producto_base pb ON pb.id = pv.id_producto_base
        WHERE vd.id_venta = %s
    """, (id_venta,))

    detalles = [
        {
            "producto": r[0],
            "cantidad": r[1],
            "precio_unitario": r[2],
            "subtotal": r[3]
        }
        for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return render_template_string(
        HTML_DETALLE_VENTA,
        venta=venta,
        detalles=detalles
    )


# --------------- REPORTE PRODUCTOS --------------

from flask import render_template_string

@app.route("/productos")
def listar_productos():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            pb.nombre            AS producto,
            pb.descripcion       AS descripcion,
            pv.marca             AS marca,
            pv.calidad           AS calidad,
            pv.subcodigo         AS subcodigo,
            pv.precio            AS precio_venta,
            pv.stock             AS stock,
            pr.nombre            AS proveedor,
            pv.ubicacion         AS ubicacion
        FROM producto_variante pv
        JOIN producto_base pb
            ON pb.id = pv.id_producto_base
        LEFT JOIN proveedor pr
            ON pr.id = pv.id_proveedor
        ORDER BY pb.nombre, pv.marca;
    """)

    productos = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Listado de productos</title>
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 6px;
                text-align: left;
            }
            th {
                background-color: #eee;
            }
            .stock-bajo {
                background-color: #ffe5e5;
            }

        </style>
    </head>
    <body>

    <h1>Listado de productos</h1>

    <table>
        <thead>
            <tr>
                <th>Producto</th>
                <th>Marca</th>
                <th>Calidad</th>
                <th>Precio</th>
                <th>Stock</th>
                <th>Proveedor</th>
            </tr>
        </thead>
        <tbody>
            {% if productos %}
                {% for p in productos %}
                <tr class="{{ 'stock-bajo' if p[6] <= 5 else '' }}">
                    <td>{{ p[0] }}</td>
                    <td>{{ p[2] }}</td>
                    <td>{{ p[3] or "-" }}</td>
                    <td>${{ p[5] }}</td>
                    <td>{{ p[6] }}</td>
                    <td>{{ p[7] or "-" }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td colspan="6">No hay productos cargados.</td>
                </tr>
            {% endif %}
        </tbody>

    </table>

    <br>
    <a href="/">Volver al inicio</a>

    </body>
    </html>
    """

    return render_template_string(html, productos=productos)


# ------------ MOSTRAR STOCK BAJO --------------------

from flask import render_template_string

STOCK_MINIMO = 5

@app.route("/stock-bajo")
def stock_bajo():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE (pb.nombre, 'producto sin base') AS producto,
            pv.marca,
            pv.calidad,
            pv.stock,
            pv.ubicacion
        FROM producto_variante pv
        LEFT JOIN producto_base pb
            ON pb.id = pv.id_producto_base
        WHERE pv.stock <= %s
        ORDER BY pv.stock ASC, pb.nombre;
    """, (STOCK_MINIMO,))

    productos = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Stock bajo</title>
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 6px;
            }
            th {
                background-color: #f2dede;
            }
            .critico {
                background-color: #f8d7da;
            }
        </style>
    </head>
    <body>

    <h1>Productos con stock bajo (≤ {{ stock_minimo }})</h1>

    {% if productos %}
        <table>
            <thead>
                <tr>
                    <th>Producto</th>
                    <th>Marca</th>
                    <th>Calidad</th>
                    <th>Stock</th>
                    <th>Ubicación</th>
                </tr>
            </thead>
            <tbody>
                {% for p in productos %}
                <tr class="{{ 'critico' if p[3] <= stock_minimo else '' }}">
                    <td>{{ p[0] }}</td>
                    <td>{{ p[1] }}</td>
                    <td>{{ p[2] or "-" }}</td>
                    <td><strong>{{ p[3] }}</strong></td>
                    <td>{{ p[4] or "-" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <p>No hay productos con stock bajo 🎉</p>
    {% endif %}

    <br>
    <a href="/">Volver al inicio</a>

    </body>
    </html>
    """

    return render_template_string(
        html,
        productos=productos,
        stock_minimo=STOCK_MINIMO
    )


# ------------------- PRODUCTOS MÁS VENDIDOS ---------------

@app.route("/productos-mas-vendidos")
def productos_mas_vendidos():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(pb.nombre, 'Producto sin base') || ' - ' ||
            COALESCE(pv.marca, 'Sin marca')           AS producto,
            SUM(vd.cantidad)                          AS cantidad_vendida,
            SUM(vd.cantidad * vd.precio_unitario)    AS total_facturado
        FROM venta_detalle vd
        LEFT JOIN producto_variante pv
            ON pv.id = vd.id_producto_variante
        LEFT JOIN producto_base pb
            ON pb.id = pv.id_producto_base
        GROUP BY producto
        ORDER BY cantidad_vendida DESC
        LIMIT 10;
    """)

    productos = cur.fetchall()

    cur.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Productos más vendidos</title>
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 6px;
                text-align: left;
            }
            th {
                background-color: #e8f0fe;
            }
        </style>
    </head>
    <body>

    <h1>Top 10 productos más vendidos</h1>

    {% if productos %}
    <table>
        <tr>
            <th>Producto</th>
            <th>Cantidad vendida</th>
            <th>Total facturado</th>
        </tr>
        {% for p in productos %}
        <tr>
            <td>{{ p[0] }}</td>
            <td>{{ p[1] }}</td>
            <td>${{ p[2] }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <p>Todavía no hay ventas registradas.</p>
    {% endif %}

    <br>
    <a href="/">Volver al inicio</a>

    </body>
    </html>
    """

    return render_template_string(html, productos=productos)

#---- PRUEBA, BORRAR DSP --------

@app.route("/test-db")
def test_db():
    try:
        conn = get_db_connection()
        conn.close()
        return "Conexión a la base OK"
    except Exception as e:
        return f"Error de conexión: {e}"




# --------------------


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
