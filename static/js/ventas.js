document.addEventListener('DOMContentLoaded', function() {
    
    const searchInput = document.getElementById('searchInput');
    const tabla = document.getElementById('tablaVentas');
    const sinResultados = document.getElementById('sinResultados');
    
    // Si no hay tabla, salir
    if (!tabla) return;
    
    const filas = tabla.querySelectorAll('tbody tr');
    
    // Búsqueda en tiempo real
    searchInput.addEventListener('input', function() {
        const busqueda = this.value.toLowerCase().trim();
        let hayResultados = false;
        
        filas.forEach(fila => {
            const textoFila = fila.textContent.toLowerCase();
            
            if (textoFila.includes(busqueda)) {
                fila.style.display = '';
                hayResultados = true;
            } else {
                fila.style.display = 'none';
            }
        });
        
        // Mostrar/ocultar mensaje de sin resultados
        if (hayResultados || busqueda === '') {
            sinResultados.style.display = 'none';
            tabla.style.display = '';
        } else {
            sinResultados.style.display = 'block';
            tabla.style.display = 'none';
        }
    });
    
});