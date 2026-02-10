document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formProveedor');
    const inputNombre = document.getElementById('nombre');
    const mensaje = document.getElementById('mensaje');
    
    form.addEventListener('submit', function(e) {
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        const nombre = inputNombre.value.trim();
        
        if (nombre === '') {
            e.preventDefault();
            mostrarMensaje('Por favor ingresá un nombre', 'error');
            inputNombre.focus();
            return false;
        }
        
        if (nombre.length < 2) {
            e.preventDefault();
            mostrarMensaje('El nombre debe tener al menos 2 caracteres', 'error');
            inputNombre.focus();
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