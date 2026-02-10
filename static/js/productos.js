document.addEventListener('DOMContentLoaded', function() {
    
    const searchInput = document.getElementById('searchInput');
    const filtroStockBajo = document.getElementById('filtroStockBajo');
    const tabla = document.getElementById('tablaProductos');
    const sinResultados = document.getElementById('sinResultados');
    const productosVisibles = document.getElementById('productosVisibles');
    
    // Si no hay tabla, salir
    if (!tabla) return;
    
    const filas = tabla.querySelectorAll('tbody tr');
    
    // Función para aplicar filtros
    function aplicarFiltros() {
        const busqueda = searchInput.value.toLowerCase().trim();
        const soloStockBajo = filtroStockBajo.checked;
        let contadorVisibles = 0;
        
        filas.forEach(fila => {
            const textoFila = fila.textContent.toLowerCase();
            const stock = parseInt(fila.dataset.stock);
            
            let cumpleBusqueda = busqueda === '' || textoFila.includes(busqueda);
            let cumpleStock = !soloStockBajo || stock <= 5;
            
            if (cumpleBusqueda && cumpleStock) {
                fila.style.display = '';
                contadorVisibles++;
            } else {
                fila.style.display = 'none';
            }
        });
        
        // Actualizar contador
        productosVisibles.textContent = contadorVisibles;
        
        // Mostrar/ocultar mensaje de sin resultados
        if (contadorVisibles > 0) {
            sinResultados.style.display = 'none';
            tabla.style.display = '';
        } else {
            sinResultados.style.display = 'block';
            tabla.style.display = 'none';
        }
    }
    
    // Eventos
    searchInput.addEventListener('input', aplicarFiltros);
    filtroStockBajo.addEventListener('change', aplicarFiltros);
    
});