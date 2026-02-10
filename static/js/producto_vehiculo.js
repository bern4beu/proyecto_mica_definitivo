document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('formProductoVehiculo');
    
    // Si no hay formulario, salir
    if (!form) return;
    
    const mensaje = document.getElementById('mensaje');
    const inputProductoBase = document.getElementById('id_producto_base');
    const selectVehiculos = document.getElementById('vehiculos');
    
    // Mejorar la experiencia del select múltiple
    selectVehiculos.addEventListener('mousedown', function(e) {
        e.preventDefault();
        
        const option = e.target;
        if (option.tagName === 'OPTION') {
            option.selected = !option.selected;
            return false;
        }
    });
    
    // Validación al enviar
    form.addEventListener('submit', function(e) {
        
        mensaje.classList.remove('show', 'exito', 'error');
        
        // Validar producto base
        if (inputProductoBase.value === '') {
            e.preventDefault();
            mostrarMensaje('Por favor seleccioná un producto base', 'error');
            inputProductoBase.focus();
            return false;
        }
        
        // Validar que haya al menos un vehículo seleccionado
        const vehiculosSeleccionados = Array.from(selectVehiculos.selectedOptions);
        
        if (vehiculosSeleccionados.length === 0) {
            e.preventDefault();
            mostrarMensaje('Por favor seleccioná al menos un vehículo', 'error');
            selectVehiculos.focus();
            return false;
        }
        
        // Mostrar cantidad de vehículos seleccionados
        const cantidad = vehiculosSeleccionados.length;
        const textoConfirmacion = cantidad === 1 
            ? '1 vehículo seleccionado' 
            : `${cantidad} vehículos seleccionados`;
        
        console.log(textoConfirmacion);
    });
    
    function mostrarMensaje(texto, tipo) {
        mensaje.textContent = texto;
        mensaje.classList.add('show', tipo);
        
        setTimeout(() => {
            mensaje.classList.remove('show');
        }, 5000);
    }
    
});