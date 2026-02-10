// Esperar a que cargue toda la página
document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formCliente');
    const inputNombre = document.getElementById('nombre');
    const mensaje = document.getElementById('mensaje');
    
    // Validar el formulario antes de enviar
    form.addEventListener('submit', function(e) {
        
        // Limpiar mensajes anteriores
        mensaje.classList.remove('show', 'exito', 'error');
        
        // Validar que el nombre no esté vacío
        const nombre = inputNombre.value.trim();
        
        if (nombre === '') {
            e.preventDefault(); // Evitar que se envíe
            mostrarMensaje('Por favor ingresá un nombre', 'error');
            inputNombre.focus();
            return false;
        }
        
        // Validar longitud mínima
        if (nombre.length < 2) {
            e.preventDefault();
            mostrarMensaje('El nombre debe tener al menos 2 caracteres', 'error');
            inputNombre.focus();
            return false;
        }
        
        // Si llegamos acá, el formulario es válido
        // Se enviará normalmente
    });
    
    // Función para mostrar mensajes
    function mostrarMensaje(texto, tipo) {
        mensaje.textContent = texto;
        mensaje.classList.add('show', tipo);
        
        // Ocultar después de 5 segundos
        setTimeout(() => {
            mensaje.classList.remove('show');
        }, 5000);
    }
    
});