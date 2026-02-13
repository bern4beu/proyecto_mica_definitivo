document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formEditarVariante');
    const mensaje = document.getElementById('mensaje');
    
    form.addEventListener('submit', function(e) {
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        const marca = document.getElementById('marca').value.trim();
        const precio = parseFloat(document.getElementById('precio').value);
        const stock = parseInt(document.getElementById('stock').value);
        
        // Validar marca
        if (marca === '') {
            e.preventDefault();
            mostrarMensaje('Por favor ingresá una marca', 'error');
            document.getElementById('marca').focus();
            return false;
        }
        
        // Validar precio
        if (isNaN(precio) || precio < 0) {
            e.preventDefault();
            mostrarMensaje('El precio debe ser mayor o igual a 0', 'error');
            document.getElementById('precio').focus();
            return false;
        }
        
        // Validar stock
        if (isNaN(stock) || stock < 0) {
            e.preventDefault();
            mostrarMensaje('El stock debe ser mayor o igual a 0', 'error');
            document.getElementById('stock').focus();
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