# ESTADO ACTUAL:
# Ventas con detalle funcionando correctamente.
# Stock se descuenta y total se calcula automáticamente.


from flask import Flask, request, render_template_string
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(database_url, sslmode="require")


@app.route("/health")
def health():
    return "OK"




# ----------- INICIO ---------------------

HTML_HOME = '''
<h1>Sistema de Gestión</h1>

<ul>
  <li><a href="/clientes">Clientes</a></li>
  <li><a href="/proveedor">Proveedores</a></li>
  <li><a href="/agregar_vehiculo">Vehículos</a></li>
  <li><a href="/producto_base">Producto base</a></li>
  <li><a href="/producto_variante">Producto variante</a></li>
  <li><a href="/producto_vehiculo">Asociar producto - vehículo</a></li>
  <li><a href="/venta">Registrar venta</a></li>
  <li><a href="/ventas">Ver ventas</a></li>
</ul>
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
        SELECT
            id,
            nombre || ' (' ||
            COALESCE(alto::text,'-') || 'x' ||
            COALESCE(ancho::text,'-') || 'x' ||
            COALESCE(largo::text,'-') || 'x' ||
            COALESCE(diametro::text,'-') || ')' AS display_name
        FROM producto_base
        ORDER BY nombre
    """)
    productos = cur.fetchall()


    cur.execute("SELECT id, nombre FROM proveedor ORDER BY nombre")
    proveedores = cur.fetchall()
    cur.close()
    conn.close()

    return render_template_string(
        HTML_FORM_VARIANTE,
        productos=productos,
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
        id_cliente = request.form['id_cliente']

        if id_cliente == "":
            id_cliente = None

        # 1) Crear venta vacía
        cur.execute(
            "INSERT INTO venta (id_cliente, total) VALUES (%s, 0) RETURNING id",
            (id_cliente,)
        )
        id_venta = cur.fetchone()[0]

        total = 0

        # 2) Procesar las 3 líneas
        for i in [1, 2, 3]:
            producto = request.form.get(f'producto_{i}')
            cantidad = request.form.get(f'cantidad_{i}')

            if producto and cantidad:
                cur.execute(
                    "SELECT precio FROM producto_variante WHERE id = %s",
                    (producto,)
                )
                precio_unitario = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO venta_detalle
                    (id_venta, id_producto_variante, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (id_venta, producto, cantidad, precio_unitario))

                total += precio_unitario * int(cantidad)

        # 3) Actualizar total
        cur.execute(
            "UPDATE venta SET total = %s WHERE id = %s",
            (total, id_venta)
        )

        conn.commit()
        cur.close()
        conn.close()

        return f"Venta registrada correctamente. Total: ${total}"

    # GET
    cur.execute("SELECT id, nombre FROM cliente ORDER BY nombre")
    clientes = cur.fetchall()

    cur.execute("""
        SELECT pv.id, pb.nombre || ' - ' || pv.marca
        FROM producto_variante pv
        JOIN producto_base pb ON pb.id = pv.id_producto_base
        ORDER BY pb.nombre
    """)
    productos = cur.fetchall()

    return render_template_string(
        HTML_FORM_VENTA,
        clientes=clientes,
        productos=productos
    )


# ----------------- LISTADO VENTA ------------------

HTML_LISTADO_VENTAS = '''
<h2>Ventas</h2>

<table border="1" cellpadding="5">
<tr>
  <th>ID</th>
  <th>Fecha</th>
  <th>Cliente</th>
  <th>Total</th>
  <th>Acción</th>
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

<br>
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

    ventas = [
        {
            "id": r[0],
            "fecha": r[1],
            "cliente": r[2],
            "total": r[3]
        }
        for r in cur.fetchall()
    ]

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