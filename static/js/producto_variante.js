document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formProductoVariante');
    
    // Si no hay formulario (no hay productos base), salir
    if (!form) return;
    
    const mensaje = document.getElementById('mensaje');
    const inputProductoBase = document.getElementById('id_producto_base');
    const inputMarca = document.getElementById('marca');
    const inputPrecio = document.getElementById('precio');
    const inputStock = document.getElementById('stock');
    
    form.addEventListener('submit', function(e) {
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        // Validar producto base
        if (inputProductoBase.value === '') {
            e.preventDefault();
            mostrarMensaje('Por favor seleccioná un producto base', 'error');
            inputProductoBase.focus();
            return false;
        }
        
        // Validar marca
        const marca = inputMarca.value.trim();
        if (marca === '') {
            e.preventDefault();
            mostrarMensaje('Por favor ingresá una marca', 'error');
            inputMarca.focus();
            return false;
        }
        
        if (marca.length < 2) {
            e.preventDefault();
            mostrarMensaje('La marca debe tener al menos 2 caracteres', 'error');
            inputMarca.focus();
            return false;
        }
        
        // Validar precio
        const precio = parseFloat(inputPrecio.value);
        if (isNaN(precio) || precio <= 0) {
            e.preventDefault();
            mostrarMensaje('El precio debe ser mayor a 0', 'error');
            inputPrecio.focus();
            return false;
        }
        
        // Validar stock
        const stock = parseInt(inputStock.value);
        if (isNaN(stock) || stock < 0) {
            e.preventDefault();
            mostrarMensaje('El stock debe ser 0 o mayor', 'error');
            inputStock.focus();
            return false;
        }
    });
    
    function mostrarMensaje(texto, tipo) {
        mensaje.textContent = texto;
        mensaje.classList.add('show', tipo);
        
        setTimeout(() => {
            mensaje.classList.remove('show');
        }, 5000);
    }
    
});