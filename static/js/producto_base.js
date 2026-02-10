document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formProductoBase');
    const inputNombre = document.getElementById('nombre');
    const mensaje = document.getElementById('mensaje');
    
    form.addEventListener('submit', function(e) {
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        const nombre = inputNombre.value.trim();
        
        if (nombre === '') {
            e.preventDefault();
            mostrarMensaje('Por favor ingresá un nombre para el producto', 'error');
            inputNombre.focus();
            return false;
        }
        
        if (nombre.length < 2) {
            e.preventDefault();
            mostrarMensaje('El nombre debe tener al menos 2 caracteres', 'error');
            inputNombre.focus();
            return false;
        }
        
        // Validar que los campos numéricos sean positivos si se completaron
        const camposNumericos = ['alto', 'ancho', 'largo', 'diametro'];
        
        for (let campo of camposNumericos) {
            const input = document.getElementById(campo);
            const valor = input.value;
            
            if (valor !== '' && parseFloat(valor) <= 0) {
                e.preventDefault();
                mostrarMensaje(`El campo ${campo} debe ser mayor a 0`, 'error');
                input.focus();
                return false;
            }
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