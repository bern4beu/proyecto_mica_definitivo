document.addEventListener('DOMContentLoaded', function() {
    
    const searchInput = document.getElementById('searchInput');
    const filtroStockBajo = document.getElementById('filtroStockBajo');
    const filtroMarca = document.getElementById('filtroMarca');
    const filtroModelo = document.getElementById('filtroModelo');
    const filtroMotor = document.getElementById('filtroMotor');
    const btnLimpiarVehiculo = document.getElementById('btnLimpiarVehiculo');
    const tabla = document.getElementById('tablaProductos');
    const sinResultados = document.getElementById('sinResultados');
    const productosVisibles = document.getElementById('productosVisibles');
    
    // Si no hay tabla, salir
    if (!tabla) return;
    
    const filas = tabla.querySelectorAll('tbody tr');
    let productosCompatibles = []; // IDs de productos compatibles con vehículo seleccionado
    
    // ========== FUNCIÓN PARA CARGAR PRODUCTOS COMPATIBLES ==========
    
    async function cargarProductosCompatibles(marca, modelo, motor) {
        if (!marca) {
            productosCompatibles = [];
            aplicarFiltros();
            return;
        }
        
        try {
            const params = new URLSearchParams({
                marca: marca
            });
            
            if (modelo) {
                params.append('modelo', modelo);
            }
            
            if (motor) {
                params.append('motor', motor);
            }
            
            const response = await fetch(`/api/productos_por_vehiculo?${params}`);
            productosCompatibles = await response.json();
            
            aplicarFiltros();
        } catch (error) {
            console.error('Error al cargar productos compatibles:', error);
        }
    }
    
    // ========== CARGAR MARCAS AL INICIO ==========
    
    cargarMarcas();
    
    async function cargarMarcas() {
        try {
            const response = await fetch('/api/marcas_vehiculo');
            const marcas = await response.json();
            
            filtroMarca.innerHTML = '<option value="">-- Todas --</option>';
            marcas.forEach(marca => {
                const option = document.createElement('option');
                option.value = marca;
                option.textContent = marca;
                filtroMarca.appendChild(option);
            });
        } catch (error) {
            console.error('Error al cargar marcas:', error);
        }
    }
    
    // ========== EVENTOS DE SELECTS EN CASCADA ==========
    
    filtroMarca.addEventListener('change', async function() {
        const marca = this.value;
        
        // Resetear modelos y motores
        filtroModelo.innerHTML = '<option value="">-- Todos --</option>';
        filtroMotor.innerHTML = '<option value="">-- Todos --</option>';
        filtroModelo.disabled = true;
        filtroMotor.disabled = true;
        productosCompatibles = [];
        
        if (!marca) {
            aplicarFiltros();
            return;
        }
        
        // Cargar productos compatibles solo con la marca
        await cargarProductosCompatibles(marca, null, null);
        
        // Cargar modelos de la marca seleccionada
        try {
            const response = await fetch(`/api/modelos_vehiculo/${encodeURIComponent(marca)}`);
            const modelos = await response.json();
            
            filtroModelo.innerHTML = '<option value="">-- Todos --</option>';
            modelos.forEach(modelo => {
                const option = document.createElement('option');
                option.value = modelo;
                option.textContent = modelo;
                filtroModelo.appendChild(option);
            });
            
            filtroModelo.disabled = false;
        } catch (error) {
            console.error('Error al cargar modelos:', error);
        }
    });
    
    filtroModelo.addEventListener('change', async function() {
        const marca = filtroMarca.value;
        const modelo = this.value;
        
        // Resetear motores
        filtroMotor.innerHTML = '<option value="">-- Todos --</option>';
        filtroMotor.disabled = true;
        
        if (!modelo) {
            productosCompatibles = [];
            aplicarFiltros();
            return;
        }
        
        // Cargar productos compatibles con marca + modelo (sin motor todavía)
        await cargarProductosCompatibles(marca, modelo, null);
        
        // Cargar motores del modelo seleccionado
        try {
            const response = await fetch(`/api/motores_vehiculo/${encodeURIComponent(marca)}/${encodeURIComponent(modelo)}`);
            const motores = await response.json();
            
            filtroMotor.innerHTML = '<option value="">-- Todos --</option>';
            motores.forEach(motor => {
                const option = document.createElement('option');
                option.value = motor;
                option.textContent = motor;
                filtroMotor.appendChild(option);
            });
            
            filtroMotor.disabled = false;
            
            // Si solo hay un motor, seleccionarlo automáticamente
            if (motores.length === 1) {
                filtroMotor.value = motores[0];
                filtroMotor.dispatchEvent(new Event('change'));
            }
        } catch (error) {
            console.error('Error al cargar motores:', error);
        }
    });
    
    filtroMotor.addEventListener('change', async function() {
        const marca = filtroMarca.value;
        const modelo = filtroModelo.value;
        const motor = this.value;
        
        if (!marca || !modelo) {
            productosCompatibles = [];
            aplicarFiltros();
            return;
        }
        
        await cargarProductosCompatibles(marca, modelo, motor);
    });
    
    // ========== LIMPIAR FILTRO DE VEHÍCULO ==========
    
    btnLimpiarVehiculo.addEventListener('click', function() {
        filtroMarca.value = '';
        filtroModelo.innerHTML = '<option value="">-- Seleccione marca --</option>';
        filtroMotor.innerHTML = '<option value="">-- Seleccione modelo --</option>';
        filtroModelo.disabled = true;
        filtroMotor.disabled = true;
        productosCompatibles = [];
        aplicarFiltros();
    });
    
    // ========== APLICAR TODOS LOS FILTROS ==========
    
    function aplicarFiltros() {
        const busqueda = searchInput.value.toLowerCase().trim();
        const soloStockBajo = filtroStockBajo.checked;
        const hayFiltroVehiculo = productosCompatibles.length > 0 || (filtroMarca.value && filtroModelo.value);
        
        let contadorVisibles = 0;
        
        filas.forEach(fila => {
            const textoFila = fila.textContent.toLowerCase();
            const stock = parseInt(fila.dataset.stock);
            const idProducto = parseInt(fila.dataset.productoid);
            
            // Filtros
            let cumpleBusqueda = busqueda === '' || textoFila.includes(busqueda);
            let cumpleStock = !soloStockBajo || stock <= 5;
            let cumpleVehiculo = !hayFiltroVehiculo || productosCompatibles.includes(idProducto);
            
            if (cumpleBusqueda && cumpleStock && cumpleVehiculo) {
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
    
    // ========== EVENTOS ==========
    
    searchInput.addEventListener('input', aplicarFiltros);
    filtroStockBajo.addEventListener('change', aplicarFiltros);
    
});