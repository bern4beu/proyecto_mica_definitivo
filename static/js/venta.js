document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formVenta');
    
    // Si no hay formulario, salir
    if (!form) return;
    
    const mensaje = document.getElementById('mensaje');
    const productosContainer = document.getElementById('productosContainer');
    const btnAgregarProducto = document.getElementById('btnAgregarProducto');
    const totalVenta = document.getElementById('totalVenta');
    const templateProducto = document.getElementById('templateProducto');
    
    let contadorProductos = 0;
    let preciosProductos = {}; // Guardamos los precios aquí
    
    // Cargar precios de productos desde el servidor
    cargarPrecios();
    
    // Agregar el primer producto al cargar la página
    agregarProducto();
    
    // Evento: Agregar producto
    btnAgregarProducto.addEventListener('click', agregarProducto);
    
    // Evento: Submit del formulario
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        // Validar que haya al menos un producto
        const productosActuales = productosContainer.querySelectorAll('.producto-item');
        
        if (productosActuales.length === 0) {
            mostrarMensaje('Debés agregar al menos un producto', 'error');
            return false;
        }
        
        // Validar que todos los productos tengan producto y cantidad
        let hayError = false;
        
        productosActuales.forEach((item, index) => {
            const select = item.querySelector('.select-producto');
            const inputCantidad = item.querySelector('.input-cantidad');
            
            if (select.value === '') {
                mostrarMensaje(`Producto ${index + 1}: Seleccioná un producto`, 'error');
                select.focus();
                hayError = true;
                return;
            }
            
            const cantidad = parseInt(inputCantidad.value);
            if (isNaN(cantidad) || cantidad < 1) {
                mostrarMensaje(`Producto ${index + 1}: La cantidad debe ser al menos 1`, 'error');
                inputCantidad.focus();
                hayError = true;
                return;
            }
        });
        
        if (hayError) return false;
        
        // Si todo está bien, enviar el formulario
        form.submit();
    });
    
    // Función: Agregar un producto
    function agregarProducto() {
        contadorProductos++;
        
        // Clonar el template
        const clone = templateProducto.content.cloneNode(true);
        
        // Actualizar los atributos name con el índice
        const select = clone.querySelector('.select-producto');
        const inputCantidad = clone.querySelector('.input-cantidad');
        
        select.name = `producto_${contadorProductos}`;
        inputCantidad.name = `cantidad_${contadorProductos}`;
        
        // Agregar al contenedor
        productosContainer.appendChild(clone);
        
        // Obtener el elemento recién agregado
        const nuevoProducto = productosContainer.lastElementChild;
        
        // Eventos para este producto
        const selectProducto = nuevoProducto.querySelector('.select-producto');
        const inputCant = nuevoProducto.querySelector('.input-cantidad');
        const btnEliminar = nuevoProducto.querySelector('.btn-eliminar');
        
        selectProducto.addEventListener('change', calcularSubtotal);
        inputCant.addEventListener('input', calcularSubtotal);
        btnEliminar.addEventListener('click', function() {
            eliminarProducto(nuevoProducto);
        });
    }
    
    // Función: Eliminar un producto
    function eliminarProducto(elemento) {
        elemento.remove();
        calcularTotal();
        
        // Si no quedan productos, agregar uno nuevo automáticamente
        const productosActuales = productosContainer.querySelectorAll('.producto-item');
        if (productosActuales.length === 0) {
            agregarProducto();
        }
    }
    
    // Función: Calcular subtotal de un producto
    function calcularSubtotal(e) {
        const productoItem = e.target.closest('.producto-item');
        const select = productoItem.querySelector('.select-producto');
        const inputCantidad = productoItem.querySelector('.input-cantidad');
        const subtotalValor = productoItem.querySelector('.subtotal-valor');
        
        const idProducto = select.value;
        const cantidad = parseInt(inputCantidad.value) || 0;
        
        if (idProducto && preciosProductos[idProducto]) {
            const precio = preciosProductos[idProducto];
            const subtotal = precio * cantidad;
            subtotalValor.textContent = subtotal.toFixed(2);
        } else {
            subtotalValor.textContent = '0.00';
        }
        
        calcularTotal();
    }
    
    // Función: Calcular total general
    function calcularTotal() {
        let total = 0;
        
        const productos = productosContainer.querySelectorAll('.producto-item');
        productos.forEach(item => {
            const select = item.querySelector('.select-producto');
            const inputCantidad = item.querySelector('.input-cantidad');
            
            const idProducto = select.value;
            const cantidad = parseInt(inputCantidad.value) || 0;
            
            if (idProducto && preciosProductos[idProducto]) {
                total += preciosProductos[idProducto] * cantidad;
            }
        });
        
        totalVenta.textContent = total.toFixed(2);
    }
    
    // Función: Cargar precios desde el servidor
    async function cargarPrecios() {
        try {
            const response = await fetch('/api/precios_productos');
            const data = await response.json();
            preciosProductos = data;
        } catch (error) {
            console.error('Error al cargar precios:', error);
            mostrarMensaje('Error al cargar precios de productos', 'error');
        }
    }
    
    // Función: Mostrar mensaje
    function mostrarMensaje(texto, tipo) {
        mensaje.textContent = texto;
        mensaje.classList.add('show', tipo);
        
        setTimeout(() => {
            mensaje.classList.remove('show');
        }, 5000);
    }
    
});