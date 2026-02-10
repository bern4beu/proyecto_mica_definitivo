document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formVehiculo');
    const inputMarca = document.getElementById('marca');
    const inputModelo = document.getElementById('modelo');
    const mensaje = document.getElementById('mensaje');
    
    form.addEventListener('submit', function(e) {
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        const marca = inputMarca.value.trim();
        const modelo = inputModelo.value.trim();
        
        if (marca === '') {
            e.preventDefault();
            mostrarMensaje('Por favor ingresá una marca', 'error');
            inputMarca.focus();
            return false;
        }
        
        if (modelo === '') {
            e.preventDefault();
            mostrarMensaje('Por favor ingresá un modelo', 'error');
            inputModelo.focus();
            return false;
        }
        
        if (marca.length < 2) {
            e.preventDefault();
            mostrarMensaje('La marca debe tener al menos 2 caracteres', 'error');
            inputMarca.focus();
            return false;
        }
        
        if (modelo.length < 2) {
            e.preventDefault();
            mostrarMensaje('El modelo debe tener al menos 2 caracteres', 'error');
            inputModelo.focus();
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