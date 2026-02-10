# ESTADO ACTUAL:
# Ventas con detalle funcionando correctamente.
# Stock se descuenta y total se calcula automáticamente.


from flask import Flask, request, render_template, jsonify
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/test")
def test():
    return "FLASK FUNCIONA"

def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(database_url, sslmode="require")

def formatear_producto_con_dimensiones(producto_tuple):
    """
    Recibe una tupla (id, nombre, alto, ancho, largo, diametro)
    y devuelve (id, nombre_formateado)
    """
    id_prod = producto_tuple[0]
    nombre = producto_tuple[1]
    alto = producto_tuple[2]
    ancho = producto_tuple[3]
    largo = producto_tuple[4]
    diametro = producto_tuple[5]
    
    if alto or ancho or largo or diametro:
        display = f"{nombre} ({alto or ''}x{ancho or ''}x{largo or ''}x{diametro or ''})"
    else:
        display = nombre
    
    return (id_prod, display)


@app.route("/health")
def health():
    return "OK"




# ----------- INICIO ---------------------


@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Estadísticas
    
    # Ventas del mes actual
    cur.execute("""
        SELECT 
            COALESCE(SUM(total), 0) as total_mes,
            COUNT(*) as cantidad
        FROM venta
        WHERE EXTRACT(MONTH FROM fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
          AND EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
    """)
    ventas_mes = cur.fetchone()
    
    # Total de productos (variantes)
    cur.execute("SELECT COUNT(*) FROM producto_variante")
    total_productos = cur.fetchone()[0]
    
    # Productos con stock bajo
    cur.execute("SELECT COUNT(*) FROM producto_variante WHERE stock <= %s", (STOCK_MINIMO,))
    stock_bajo = cur.fetchone()[0]
    
    # Total de clientes
    cur.execute("SELECT COUNT(*) FROM cliente")
    total_clientes = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    stats = {
        "ventas_mes": f"{ventas_mes[0]:.2f}",
        "cantidad_ventas": ventas_mes[1],
        "total_productos": total_productos,
        "stock_bajo": stock_bajo,
        "total_clientes": total_clientes
    }
    
    return render_template('home.html', stats=stats)


# ---------- CLIENTES ----------


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
        
        # Renderizar el mismo template pero con mensaje de éxito
        return render_template('clientes.html', 
                             mensaje_exito=f'Cliente "{nombre}" agregado con éxito!')
    
    # GET: mostrar el formulario
    return render_template('clientes.html')


# ---------- VEHICULOS ----------


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
            mensaje_exito = f'Vehículo {marca} {modelo} agregado con éxito!'
        
        except Exception as e:
            conn.rollback()
            mensaje_exito = None
            mensaje_error = f"Error al guardar vehículo: {e}"
        
        finally:
            cur.close()
            conn.close()
        
        return render_template('vehiculo.html', 
                             mensaje_exito=mensaje_exito)
    
    return render_template('vehiculo.html')


# ---------- PRODUCTO BASE ----------

def to_numeric_or_none(value):
    return value if value != '' else None



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
        
        return render_template('producto_base.html',
                             mensaje_exito=f'Producto base "{nombre}" agregado con éxito!')
    
    return render_template('producto_base.html')


# --------- PRODUCTO BASE ↔ VEHICULO ----------



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
        
        cantidad = len(ids_vehiculos)
        mensaje = f'{cantidad} vehículo(s) asociado(s) correctamente!'
        
        # Recargar datos
        cur.execute("""
            SELECT id, nombre, alto, ancho, largo, diametro 
            FROM producto_base 
            ORDER BY nombre
        """)
        productos = [formatear_producto_con_dimensiones(p) for p in cur.fetchall()]
        
        cur.execute("SELECT id, marca, modelo, motor FROM vehiculo ORDER BY marca, modelo")
        vehiculos = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('producto_vehiculo.html',
                             productos=productos,
                             vehiculos=vehiculos,
                             mensaje_exito=mensaje)

    # GET
    cur.execute("""
        SELECT id, nombre, alto, ancho, largo, diametro 
        FROM producto_base 
        ORDER BY nombre
    """)
    productos = [formatear_producto_con_dimensiones(p) for p in cur.fetchall()]

    cur.execute("SELECT id, marca, modelo, motor FROM vehiculo ORDER BY marca, modelo")
    vehiculos = cur.fetchall()
    
    cur.close()
    conn.close()

    return render_template('producto_vehiculo.html',
                         productos=productos,
                         vehiculos=vehiculos)



# ---------- PROVEEDORES ----------


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
        
        return render_template('proveedor.html', 
                             mensaje_exito=f'Proveedor "{nombre}" agregado con éxito!')
    
    return render_template('proveedor.html')


# ---------- PRODUCTO VARIANTE ----------


from psycopg2 import errors

@app.route('/producto_variante', methods=['GET', 'POST'])
def agregar_producto_variante():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        mensaje_exito = None
        mensaje_error = None
        
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
            mensaje_exito = f'Producto variante "{request.form["marca"]}" agregado con éxito!'
            
        except errors.UniqueViolation:
            conn.rollback()
            mensaje_error = 'Error: ya existe un producto variante con ese Producto Base y Marca.'
        
        # Recargar datos para mostrar el formulario de nuevo
        cur.execute("""
            SELECT id, nombre, alto, ancho, largo, diametro
            FROM producto_base
            ORDER BY nombre
        """)
        productos = cur.fetchall()
        
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
        
        return render_template('producto_variante.html',
                             productos=productos_para_select,
                             proveedores=proveedores,
                             mensaje_exito=mensaje_exito,
                             mensaje_error=mensaje_error)

    # GET
    cur.execute("""
        SELECT id, nombre, alto, ancho, largo, diametro
        FROM producto_base
        ORDER BY nombre
    """)
    productos = cur.fetchall()

    # SI NO HAY PRODUCTOS BASE
    if not productos:
        cur.close()
        conn.close()
        return render_template('producto_variante.html',
                             productos=None,
                             proveedores=None)

    # Construir lista para el select
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

    return render_template('producto_variante.html',
                         productos=productos_para_select,
                         proveedores=proveedores)

# ------------------ VENTA ------------------------------



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

        # Obtener todos los productos enviados (dinámicamente)
        productos_enviados = {}
        for key in request.form.keys():
            if key.startswith('producto_'):
                index = key.split('_')[1]
                productos_enviados[index] = {
                    'producto': request.form.get(f'producto_{index}'),
                    'cantidad': request.form.get(f'cantidad_{index}')
                }

        # Procesar cada producto
        for index, datos in productos_enviados.items():
            id_producto = datos['producto']
            cantidad = datos['cantidad']

            if id_producto and cantidad:
                cur.execute(
                    "SELECT precio FROM producto_variante WHERE id = %s",
                    (id_producto,)
                )
                row = cur.fetchone()

                if not row:
                    continue  # producto inválido, lo salteamos

                precio_unitario = row[0]

                cur.execute("""
                    INSERT INTO venta_detalle
                    (id_venta, id_producto_variante, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (id_venta, id_producto, cantidad, precio_unitario))

                total += precio_unitario * int(cantidad)
                hay_productos = True

        if not hay_productos:
            conn.rollback()
            cur.close()
            conn.close()
            
            # Recargar datos para mostrar el formulario de nuevo
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT id, nombre FROM cliente ORDER BY nombre")
            clientes = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    pv.id, 
                    pb.nombre,
                    pv.marca,
                    pb.alto,
                    pb.ancho,
                    pb.largo,
                    pb.diametro
                FROM producto_variante pv
                JOIN producto_base pb ON pb.id = pv.id_producto_base
                ORDER BY pb.nombre, pv.marca
            """)
            
            productos = []
            for p in cur.fetchall():
                id_var = p[0]
                nombre = p[1]
                marca = p[2]
                alto, ancho, largo, diametro = p[3], p[4], p[5], p[6]
                
                if alto or ancho or largo or diametro:
                    display = f"{nombre} ({alto or ''}x{ancho or ''}x{largo or ''}x{diametro or ''}) - {marca}"
                else:
                    display = f"{nombre} - {marca}"
                
                productos.append((id_var, display))
            
            cur.close()
            conn.close()
            
            return render_template('venta.html',
                                 clientes=clientes,
                                 productos=productos,
                                 mensaje_error='No se puede registrar una venta sin productos')

        cur.execute(
            "UPDATE venta SET total = %s WHERE id = %s",
            (total, id_venta)
        )

        conn.commit()
        cur.close()
        conn.close()

        # Redirigir a la página de ventas con mensaje de éxito
        return f'''
        <div style="font-family: Arial; padding: 40px; text-align: center;">
            <div style="background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto;">
                <h2>✓ Venta registrada correctamente</h2>
                <p style="font-size: 24px; margin: 20px 0;">Total: <strong>${total}</strong></p>
            </div>
            <br>
            <a href="/venta" style="background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Registrar otra venta</a>
            <br><br>
            <a href="/ventas" style="background: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Ver todas las ventas</a>
            <br><br>
            <a href="/" style="color: #666; text-decoration: none;">Volver al inicio</a>
        </div>
        '''

    # -------- GET --------

    cur.execute("SELECT id, nombre FROM cliente ORDER BY nombre")
    clientes = cur.fetchall()

    cur.execute("""
        SELECT 
            pv.id, 
            pb.nombre,
            pv.marca,
            pb.alto,
            pb.ancho,
            pb.largo,
            pb.diametro
        FROM producto_variante pv
        JOIN producto_base pb ON pb.id = pv.id_producto_base
        ORDER BY pb.nombre, pv.marca
    """)

    productos = []
    for p in cur.fetchall():
        id_var = p[0]
        nombre = p[1]
        marca = p[2]
        alto, ancho, largo, diametro = p[3], p[4], p[5], p[6]
        
        if alto or ancho or largo or diametro:
            display = f"{nombre} ({alto or ''}x{ancho or ''}x{largo or ''}x{diametro or ''}) - {marca}"
        else:
            display = f"{nombre} - {marca}"
        
        productos.append((id_var, display))

    if not productos:
        cur.close()
        conn.close()
        return render_template('venta.html',
                             clientes=None,
                             productos=None)

    cur.close()
    conn.close()

    return render_template('venta.html',
                         clientes=clientes,
                         productos=productos)



# ----------------- LISTADO VENTA ------------------


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
            "total": f"{r[3]:.2f}"
        })

    cur.close()
    conn.close()

    return render_template('ventas.html', ventas=ventas)


# ------------------- DETALLE VENTA ---------------------


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
    
    if not v:
        return '''
        <div style="font-family: Arial; padding: 40px; text-align: center;">
            <h2>Venta no encontrada</h2>
            <a href="/ventas">Volver a ventas</a>
        </div>
        '''

    venta = {
        "id": v[0],
        "fecha": v[1].strftime("%d/%m/%Y %H:%M"),
        "cliente": v[2],
        "total": f"{v[3]:.2f}"
    }

    # Detalle de la venta
    cur.execute("""
        SELECT
            pb.nombre,
            pv.marca,
            pb.alto,
            pb.ancho,
            pb.largo,
            pb.diametro,
            vd.cantidad,
            vd.precio_unitario,
            vd.cantidad * vd.precio_unitario AS subtotal
        FROM venta_detalle vd
        JOIN producto_variante pv ON pv.id = vd.id_producto_variante
        JOIN producto_base pb ON pb.id = pv.id_producto_base
        WHERE vd.id_venta = %s
    """, (id_venta,))

    detalles = []
    for r in cur.fetchall():
        nombre = r[0]
        marca = r[1]
        alto, ancho, largo, diametro = r[2], r[3], r[4], r[5]
        cantidad = r[6]
        precio_unitario = r[7]
        subtotal = r[8]
        
        # Formatear nombre con dimensiones
        if alto or ancho or largo or diametro:
            producto_display = f"{nombre} ({alto or ''}x{ancho or ''}x{largo or ''}x{diametro or ''}) - {marca}"
        else:
            producto_display = f"{nombre} - {marca}"
        
        detalles.append({
            "producto": producto_display,
            "cantidad": cantidad,
            "precio_unitario": f"{precio_unitario:.2f}",
            "subtotal": f"{subtotal:.2f}"
        })

    cur.close()
    conn.close()

    return render_template('detalle_venta.html',
                         venta=venta,
                         detalles=detalles)

# --------------- REPORTE PRODUCTOS --------------


@app.route("/productos")
def listar_productos():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            pv.id                AS id_variante,
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

    productos = []
    for r in cur.fetchall():
        productos.append({
            "id": r[0],
            "producto": r[1],
            "descripcion": r[2],
            "marca": r[3],
            "calidad": r[4],
            "subcodigo": r[5],
            "precio": f"{r[6]:.2f}",
            "stock": r[7],
            "proveedor": r[8],
            "ubicacion": r[9]
        })

    cur.close()
    conn.close()

    return render_template('productos.html',
                         productos=productos)


# ------------ MOSTRAR STOCK BAJO --------------------


STOCK_MINIMO = 5

@app.route("/stock-bajo")
def stock_bajo():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(pb.nombre, 'producto sin base') AS producto,
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

    productos = []
    for r in cur.fetchall():
        productos.append({
            "producto": r[0],
            "marca": r[1],
            "calidad": r[2],
            "stock": r[3],
            "ubicacion": r[4]
        })

    cur.close()
    conn.close()

    return render_template('stock_bajo.html',
                         productos=productos,
                         stock_minimo=STOCK_MINIMO)


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

    productos = []
    for r in cur.fetchall():
        productos.append({
            "producto": r[0],
            "cantidad_vendida": r[1],
            "total_facturado": f"{r[2]:.2f}"
        })

    cur.close()
    conn.close()

    return render_template('productos_mas_vendidos.html',
                         productos=productos)

#---- PRUEBA, BORRAR DSP --------

@app.route("/test-db")
def test_db():
    try:
        conn = get_db_connection()
        conn.close()
        return "Conexión a la base OK"
    except Exception as e:
        return f"Error de conexión: {e}"


# --------- ENDPOINT API PARA PRECIOS ---------------

@app.route('/api/precios_productos')
def api_precios_productos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, precio FROM producto_variante")
    precios = {str(row[0]): float(row[1]) for row in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    from flask import jsonify
    return jsonify(precios)



# ============ APIs para filtros de vehículos ============

@app.route('/api/marcas_vehiculo')
def api_marcas_vehiculo():
    """Devuelve todas las marcas de vehículos únicas"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT marca 
        FROM vehiculo 
        ORDER BY marca
    """)
    
    marcas = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(marcas)


@app.route('/api/modelos_vehiculo/<marca>')
def api_modelos_vehiculo(marca):
    """Devuelve los modelos de una marca específica"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT modelo 
        FROM vehiculo 
        WHERE marca = %s
        ORDER BY modelo
    """, (marca,))
    
    modelos = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(modelos)


@app.route('/api/motores_vehiculo/<marca>/<modelo>')
def api_motores_vehiculo(marca, modelo):
    """Devuelve los motores de una marca y modelo específicos"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT motor 
        FROM vehiculo 
        WHERE marca = %s AND modelo = %s
        ORDER BY motor
    """, (marca, modelo))
    
    motores = [row[0] if row[0] else 'Sin motor especificado' for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(motores)


@app.route('/api/productos_por_vehiculo')
def api_productos_por_vehiculo():
    """Devuelve IDs de productos variantes compatibles con un vehículo específico"""
    marca = request.args.get('marca')
    modelo = request.args.get('modelo', None)
    motor = request.args.get('motor', None)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Construir query dinámicamente
    query = """
        SELECT DISTINCT pv.id
        FROM producto_variante pv
        JOIN producto_vehiculo pve ON pve.id_producto_base = pv.id_producto_base
        JOIN vehiculo v ON v.id = pve.id_vehiculo
        WHERE v.marca = %s
    """
    
    params = [marca]
    
    # Si hay modelo, agregarlo al filtro
    if modelo:
        query += " AND v.modelo = %s"
        params.append(modelo)
    
    # Si hay motor, agregarlo al filtro
    if motor:
        if motor == 'Sin motor especificado':
            query += " AND v.motor IS NULL"
        else:
            query += " AND v.motor = %s"
            params.append(motor)
    
    cur.execute(query, params)
    
    ids = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify(ids)

# ------ FIN --------------


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
