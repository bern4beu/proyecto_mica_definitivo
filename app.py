# ESTADO ACTUAL:
# Ventas con detalle funcionando correctamente.
# Stock se descuenta y total se calcula automáticamente.


from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)

# Clave secreta para sesiones (necesaria para Flask-Login)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-desarrollo-cambiar-en-produccion')

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirigir al login si no está autenticado
login_manager.login_message = 'Iniciá sesión para acceder al sistema'

# ============ CLASE USUARIO ============

class Usuario(UserMixin):
    """
    Clase que representa un usuario logueado.
    UserMixin agrega métodos necesarios para Flask-Login:
    - is_authenticated
    - is_active
    - get_id()
    """
    def __init__(self, id, nombre, email, rol, activo):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.rol = rol
        self.activo = activo
    
    def es_admin(self):
        return self.rol == 'admin'


@login_manager.user_loader
def cargar_usuario(user_id):
    """
    Flask-Login llama a esta función en cada request
    para cargar el usuario desde la DB usando el ID guardado en la sesión.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, nombre, email, rol, activo 
        FROM usuario 
        WHERE id = %s AND activo = TRUE
    """, (user_id,))
    
    u = cur.fetchone()
    cur.close()
    conn.close()
    
    if u:
        return Usuario(u[0], u[1], u[2], u[3], u[4])
    return None



@app.route("/test")
def test():
    return "FLASK FUNCIONA"

# ----------------------------------------------

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

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

def normalizar_texto(texto):
    """
    Normaliza un texto: capitaliza primera letra de cada palabra, 
    quita espacios extras, y convierte a title case.
    """
    if not texto:
        return texto
    
    # Quitar espacios al inicio y final
    texto = texto.strip()
    
    # Quitar múltiples espacios
    import re
    texto = re.sub(r'\s+', ' ', texto)
    
    # Capitalizar cada palabra (Title Case)
    texto = texto.title()
    
    return texto


def encontrar_similitud(texto, lista_existentes):
    """
    Busca si hay algún texto similar en la lista.
    Solo retorna coincidencia si es EXACTA (ignorando mayúsculas/minúsculas).
    Retorna el texto similar si existe, o None.
    """
    if not texto or not lista_existentes:
        return None
    
    texto_lower = texto.lower().strip()
    
    for existente in lista_existentes:
        existente_lower = existente.lower().strip()
        
        # Solo coincidencia EXACTA (ignorando mayúsculas)
        if texto_lower == existente_lower:
            return existente
    
    return None

# ---------------------------------

@app.route("/health")
def health():
    return "OK"



# ============ LOGIN / LOGOUT ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, redirigir al inicio
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, nombre, email, password_hash, rol, activo
            FROM usuario
            WHERE email = %s
        """, (email,))
        
        u = cur.fetchone()
        cur.close()
        conn.close()
        
        # Verificar usuario y contraseña
        if not u:
            return render_template('login.html',
                                 error='Email o contraseña incorrectos')
        
        if not u[5]:  # activo = FALSE
            return render_template('login.html',
                                 error='Tu cuenta está desactivada. Contactá al administrador')
        
        if not check_password_hash(u[3], password):
            return render_template('login.html',
                                 error='Email o contraseña incorrectos')
        
        # Login exitoso
        usuario = Usuario(u[0], u[1], u[2], u[4], u[5])
        login_user(usuario, remember=True)
        
        # Redirigir a la página que intentaba visitar, o al inicio
        next_page = request.args.get('next')
        return redirect(next_page or url_for('home'))
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



# ----------- INICIO ---------------------


@app.route('/')
@login_required
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

# ----- CAMBIAR PASSWORD --------

@app.route('/cambiar_password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    error = None
    exito = None
    
    if request.method == 'POST':
        password_actual = request.form['password_actual']
        password_nuevo = request.form['password_nuevo']
        password_confirmar = request.form['password_confirmar']
        
        # Validaciones
        if password_nuevo != password_confirmar:
            error = 'Las contraseñas nuevas no coinciden'
        
        elif len(password_nuevo) < 8:
            error = 'La nueva contraseña debe tener al menos 8 caracteres'
        
        else:
            # Verificar contraseña actual
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT password_hash FROM usuario WHERE id = %s
            """, (current_user.id,))
            
            u = cur.fetchone()
            
            if not check_password_hash(u[0], password_actual):
                error = 'La contraseña actual es incorrecta'
                cur.close()
                conn.close()
            else:
                # Actualizar contraseña
                nuevo_hash = generate_password_hash(password_nuevo)
                
                cur.execute("""
                    UPDATE usuario SET password_hash = %s WHERE id = %s
                """, (nuevo_hash, current_user.id))
                
                conn.commit()
                cur.close()
                conn.close()
                
                exito = '¡Contraseña actualizada correctamente!'
    
    return render_template('cambiar_password.html',
                         error=error,
                         exito=exito)


# ---------- CLIENTES ----------


@app.route('/clientes', methods=['GET', 'POST'])
@login_required
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
@login_required
def agregar_vehiculo():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == "POST":
        marca_raw = request.form["marca"]
        modelo_raw = request.form["modelo"]
        motor_raw = request.form["motor"] or None
        
        # Obtener marcas y modelos existentes
        cur.execute("SELECT DISTINCT marca FROM vehiculo")
        marcas_existentes = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT DISTINCT modelo FROM vehiculo")
        modelos_existentes = [row[0] for row in cur.fetchall()]
        
        # Normalizar
        marca = normalizar_texto(marca_raw)
        modelo = normalizar_texto(modelo_raw)
        motor = normalizar_texto(motor_raw) if motor_raw else None
        
        # Buscar similitudes
        marca_similar = encontrar_similitud(marca, marcas_existentes)
        modelo_similar = encontrar_similitud(modelo, modelos_existentes)
        
        mensaje_exito = None
        mensaje_advertencia = None
        
        # Si hay similitudes, usar las existentes
        if marca_similar and marca != marca_similar:
            mensaje_advertencia = f'Se normalizó "{marca_raw}" a "{marca_similar}" (ya existente)'
            marca = marca_similar
        
        if modelo_similar and modelo != modelo_similar:
            if mensaje_advertencia:
                mensaje_advertencia += f' y "{modelo_raw}" a "{modelo_similar}"'
            else:
                mensaje_advertencia = f'Se normalizó "{modelo_raw}" a "{modelo_similar}" (ya existente)'
            modelo = modelo_similar
        
        try:
            cur.execute("""
                INSERT INTO vehiculo (marca, modelo, motor)
                VALUES (%s, %s, %s)
            """, (marca, modelo, motor))
            conn.commit()
            
            mensaje_exito = f'Vehículo {marca} {modelo} agregado con éxito!'
            if mensaje_advertencia:
                mensaje_exito += f' ({mensaje_advertencia})'
        
        except Exception as e:
            conn.rollback()
            mensaje_error = f"Error: {e}"
            
            # Recargar listas para mostrar formulario de nuevo
            cur.execute("SELECT DISTINCT marca FROM vehiculo ORDER BY marca")
            marcas_existentes = [row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT DISTINCT modelo FROM vehiculo ORDER BY modelo")
            modelos_existentes = [row[0] for row in cur.fetchall()]
            
            cur.close()
            conn.close()
            
            return render_template('vehiculo.html',
                                 marcas_existentes=marcas_existentes,
                                 modelos_existentes=modelos_existentes,
                                 mensaje_error=mensaje_error)
        
        # Recargar listas actualizadas
        cur.execute("SELECT DISTINCT marca FROM vehiculo ORDER BY marca")
        marcas_existentes = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT DISTINCT modelo FROM vehiculo ORDER BY modelo")
        modelos_existentes = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return render_template('vehiculo.html',
                             marcas_existentes=marcas_existentes,
                             modelos_existentes=modelos_existentes,
                             mensaje_exito=mensaje_exito)
    
    # GET: Cargar listas existentes
    cur.execute("SELECT DISTINCT marca FROM vehiculo ORDER BY marca")
    marcas_existentes = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT modelo FROM vehiculo ORDER BY modelo")
    modelos_existentes = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return render_template('vehiculo.html',
                         marcas_existentes=marcas_existentes,
                         modelos_existentes=modelos_existentes)


# ---------- PRODUCTO BASE ----------

def to_numeric_or_none(value):
    return value if value != '' else None



@app.route('/producto_base', methods=['GET', 'POST'])
@login_required
def agregar_producto_base():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        alto = to_numeric_or_none(request.form['alto'])
        ancho = to_numeric_or_none(request.form['ancho'])
        largo = to_numeric_or_none(request.form['largo'])
        diametro = to_numeric_or_none(request.form['diametro'])
        
        imagen_url = None
        
        # Manejar imagen si se subió una
        imagen = request.files.get('imagen')
        if imagen and imagen.filename:
            try:
                supabase = get_supabase_client()
                
                # Crear nombre único para el archivo
                import uuid
                extension = imagen.filename.rsplit('.', 1)[-1].lower()
                nombre_archivo = f"base_{uuid.uuid4().hex}.{extension}"
                
                # Subir imagen a Supabase Storage
                imagen_bytes = imagen.read()
                supabase.storage.from_('productos').upload(
                    nombre_archivo,
                    imagen_bytes,
                    {"content-type": imagen.content_type}
                )
                
                # Obtener URL pública
                imagen_url = supabase.storage.from_('productos').get_public_url(nombre_archivo)
                
            except Exception as e:
                print(f"Error al subir imagen: {e}")
                imagen_url = None
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO producto_base
            (nombre, descripcion, alto, ancho, largo, diametro, imagen_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, descripcion, alto, ancho, largo, diametro, imagen_url))
        conn.commit()
        cur.close()
        conn.close()
        
        return render_template('producto_base.html',
                             mensaje_exito=f'Producto base "{nombre}" agregado con éxito!')
    
    return render_template('producto_base.html')


# --------- PRODUCTO BASE ↔ VEHICULO ----------



@app.route('/producto_vehiculo', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
            pv.ubicacion         AS ubicacion,
            pv.imagen_url        AS imagen_url,
            pv.codigo            AS codigo   
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
            "ubicacion": r[9],
            "imagen_url": r[10],
            "codigo": r[11]
        })

    cur.close()
    conn.close()

    return render_template('productos.html',
                         productos=productos)


# ------------ MOSTRAR STOCK BAJO --------------------


STOCK_MINIMO = 5

@app.route("/stock-bajo")
@login_required
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
@login_required
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
@login_required
def test_db():
    try:
        conn = get_db_connection()
        conn.close()
        return "Conexión a la base OK"
    except Exception as e:
        return f"Error de conexión: {e}"


# --------- ENDPOINT API PARA PRECIOS ---------------

@app.route('/api/precios_productos')
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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


# =============== EDITAR PRODUCTO VARIANTE ===============

@app.route('/editar_variante/<int:id_variante>', methods=['GET', 'POST'])
@login_required
def editar_variante(id_variante):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        # Inicializar variables SIEMPRE al principio
        mensaje_exito = None
        mensaje_error = None
        imagen_url = None
        
        marca = normalizar_texto(request.form['marca'])
        calidad = request.form['calidad'] or None
        precio = request.form['precio']
        precio_compra = request.form['precio_compra'] or None
        stock = request.form['stock']
        ubicacion = request.form['ubicacion'] or None
        id_proveedor = request.form['id_proveedor'] or None
        
        # Manejar imagen si se subió una
        imagen = request.files.get('imagen')
        print(f"DEBUG - Imagen recibida: {imagen}")
        print(f"DEBUG - Filename: {imagen.filename if imagen else 'None'}")

        if imagen and imagen.filename:
            try:
                supabase = get_supabase_client()
                print(f"DEBUG - Supabase client creado: {supabase}")
                
                import uuid
                extension = imagen.filename.rsplit('.', 1)[-1].lower()
                nombre_archivo = f"variante_{id_variante}_{uuid.uuid4().hex}.{extension}"
                print(f"DEBUG - Nombre archivo: {nombre_archivo}")
                
                imagen_bytes = imagen.read()
                print(f"DEBUG - Tamaño imagen: {len(imagen_bytes)} bytes")
                
                resultado = supabase.storage.from_('productos').upload(
                    nombre_archivo,
                    imagen_bytes,
                    {"content-type": imagen.content_type}
                )
                print(f"DEBUG - Resultado upload: {resultado}")
                
                imagen_url = supabase.storage.from_('productos').get_public_url(nombre_archivo)
                print(f"DEBUG - URL generada: {imagen_url}")
                
            except Exception as e:
                print(f"ERROR al subir imagen: {e}")
                import traceback
                traceback.print_exc()
        
        try:
            if imagen_url:
                cur.execute("""
                    UPDATE producto_variante
                    SET marca = %s,
                        calidad = %s,
                        precio = %s,
                        precio_compra = %s,
                        stock = %s,
                        ubicacion = %s,
                        id_proveedor = %s,
                        imagen_url = %s
                    WHERE id = %s
                """, (marca, calidad, precio, precio_compra,
                    stock, ubicacion, id_proveedor, imagen_url, id_variante))
            else:
                cur.execute("""
                    UPDATE producto_variante
                    SET marca = %s,
                        calidad = %s,
                        precio = %s,
                        precio_compra = %s,
                        stock = %s,
                        ubicacion = %s,
                        id_proveedor = %s
                    WHERE id = %s
                """, (marca, calidad, precio, precio_compra,
                    stock, ubicacion, id_proveedor, id_variante))
            
            conn.commit()
            mensaje_exito = '¡Producto actualizado correctamente!'
            
        except Exception as e:
            conn.rollback()
            mensaje_error = f'Error al actualizar: {e}'
        
        # Recargar datos actualizados
        cur.execute("""
            SELECT
                pv.id,
                pb.nombre AS producto_base,
                pv.marca,
                pv.calidad,
                pv.precio,
                pv.precio_compra,
                pv.stock,
                pv.ubicacion,
                pv.id_proveedor,
                pv.imagen_url
            FROM producto_variante pv
            JOIN producto_base pb ON pb.id = pv.id_producto_base
            WHERE pv.id = %s
        """, (id_variante,))

        v = cur.fetchone()
        variante = {
            "id": v[0],
            "producto_base": v[1],
            "marca": v[2],
            "calidad": v[3],
            "precio": v[4],
            "precio_compra": v[5],
            "stock": v[6],
            "ubicacion": v[7],
            "id_proveedor": v[8],
            "imagen_url": v[9]
        }
        
        cur.execute("SELECT id, nombre FROM proveedor ORDER BY nombre")
        proveedores = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('editar_variante.html',
                             variante=variante,
                             proveedores=proveedores,
                             mensaje_exito=mensaje_exito,
                             mensaje_error=mensaje_error)
    
    # GET: Cargar datos del producto
    cur.execute("""
        SELECT
            pv.id,
            pb.nombre AS producto_base,
            pv.marca,
            pv.calidad,
            pv.precio,
            pv.precio_compra,
            pv.stock,
            pv.ubicacion,
            pv.id_proveedor
        FROM producto_variante pv
        JOIN producto_base pb ON pb.id = pv.id_producto_base
        WHERE pv.id = %s
    """, (id_variante,))
    
    v = cur.fetchone()
    
    # Si no existe el producto
    if not v:
        cur.close()
        conn.close()
        return '''
        <div style="font-family: Arial; padding: 40px; text-align: center;">
            <h2>Producto no encontrado</h2>
            <a href="/productos">Volver a productos</a>
        </div>
        '''
    
    variante = {
        "id": v[0],
        "producto_base": v[1],
        "marca": v[2],
        "calidad": v[3],
        "precio": v[4],
        "precio_compra": v[5],
        "stock": v[6],
        "ubicacion": v[7],
        "id_proveedor": v[8]
    }
    
    cur.execute("SELECT id, nombre FROM proveedor ORDER BY nombre")
    proveedores = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('editar_variante.html',
                         variante=variante,
                         proveedores=proveedores)



# ============ GESTIÓN DE USUARIOS (solo admin) ============

def solo_admin(f):
    """Decorador que permite acceso solo a admins"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin():
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/usuarios')
@login_required
@solo_admin
def listar_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, nombre, email, rol, activo,
               TO_CHAR(creado_en, 'DD/MM/YYYY') as creado_en
        FROM usuario
        ORDER BY creado_en DESC
    """)
    
    usuarios = []
    for u in cur.fetchall():
        usuarios.append({
            "id": u[0],
            "nombre": u[1],
            "email": u[2],
            "rol": u[3],
            "activo": u[4],
            "creado_en": u[5]
        })
    
    cur.close()
    conn.close()
    
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/usuarios/crear', methods=['POST'])
@login_required
@solo_admin
def crear_usuario():
    nombre = request.form['nombre'].strip()
    email = request.form['email'].strip().lower()
    password = request.form['password']
    rol = request.form['rol']
    
    # Validaciones
    if len(password) < 8:
        return redirect(url_for('listar_usuarios') + '?error=La contraseña debe tener al menos 8 caracteres')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        password_hash = generate_password_hash(password)
        
        cur.execute("""
            INSERT INTO usuario (nombre, email, password_hash, rol)
            VALUES (%s, %s, %s, %s)
        """, (nombre, email, password_hash, rol))
        
        conn.commit()
        mensaje = f'Usuario {nombre} creado correctamente'
        
    except Exception as e:
        conn.rollback()
        mensaje = f'Error: ese email ya existe'
    
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('listar_usuarios',
                           mensaje_exito=mensaje))


@app.route('/usuarios/desactivar/<int:id_usuario>')
@login_required
@solo_admin
def desactivar_usuario(id_usuario):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE usuario SET activo = FALSE WHERE id = %s
    """, (id_usuario,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('listar_usuarios'))


@app.route('/usuarios/activar/<int:id_usuario>')
@login_required
@solo_admin
def activar_usuario(id_usuario):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE usuario SET activo = TRUE WHERE id = %s
    """, (id_usuario,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('listar_usuarios'))


# ------ FIN --------------


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
