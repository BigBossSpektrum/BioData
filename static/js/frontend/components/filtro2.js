document.addEventListener('DOMContentLoaded', function () {
    const inputTexto = document.getElementById('filtroUsuarios');
    const inputDesde = document.getElementById('filtroDesde');
    const inputHasta = document.getElementById('filtroHasta');
    const filas = Array.from(document.querySelectorAll('tbody tr')).filter(f => !f.id);
    const sinCoincidencias = document.getElementById('sinCoincidencias');

    function aplicarFiltros() {
        const texto = inputTexto.value.toLowerCase();
        const desde = inputDesde.value;
        const hasta = inputHasta.value;
        let visibles = 0;

        filas.forEach(fila => {
            const textoFila = fila.textContent.toLowerCase();
            const celdaFecha = fila.querySelector('.col-dia');
            const fechaTexto = celdaFecha ? celdaFecha.textContent.trim() : '';

            let visible = true;

            // Filtro de texto
            if (texto && !textoFila.includes(texto)) {
                visible = false;
            }

            // Filtro por fecha
            if (fechaTexto) {
                const fecha = new Date(fechaTexto);
                const desdeDate = desde ? new Date(desde) : null;
                const hastaDate = hasta ? new Date(hasta) : null;

                if (desdeDate && fecha < desdeDate) visible = false;
                if (hastaDate && fecha > hastaDate) visible = false;
            } else if (desde || hasta) {
                // Si hay filtro de fecha pero la fila no tiene fecha, ocultar fila
                visible = false;
            }

            fila.style.display = visible ? '' : 'none';
            if (visible) visibles++;
        });

        sinCoincidencias.style.display = visibles === 0 ? '' : 'none';
    }

    // Función para actualizar URL con filtros y recargar la página
    function aplicarFiltrosConPaginacion() {
        const params = new URLSearchParams(window.location.search);
        
        // Mantener filtros existentes (nombre, cedula, estacion, fecha_inicio, fecha_fin)
        // y agregar los nuevos filtros de búsqueda
        if (inputTexto.value.trim()) {
            params.set('search', inputTexto.value.trim());
        } else {
            params.delete('search');
        }
        
        if (inputDesde.value) {
            params.set('fecha_desde', inputDesde.value);
        } else {
            params.delete('fecha_desde');
        }
        
        if (inputHasta.value) {
            params.set('fecha_hasta', inputHasta.value);
        } else {
            params.delete('fecha_hasta');
        }
        
        // Resetear a la primera página cuando se aplican filtros
        params.set('page', '1');
        
        const newUrl = window.location.pathname + '?' + params.toString();
        window.location.href = newUrl;
    }

    // Aplicar filtros inmediatamente para la página actual (sin recargar)
    inputTexto.addEventListener('input', aplicarFiltros);
    inputDesde.addEventListener('change', aplicarFiltros);
    inputHasta.addEventListener('change', aplicarFiltros);

    // Aplicar filtros con paginación después de un breve delay para evitar múltiples recargas
    let timeoutId;
    inputTexto.addEventListener('input', function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(aplicarFiltrosConPaginacion, 1000); // 1 segundo de delay
    });

    inputDesde.addEventListener('change', aplicarFiltrosConPaginacion);
    inputHasta.addEventListener('change', aplicarFiltrosConPaginacion);

    // Aplicar filtros iniciales
    aplicarFiltros();
});
