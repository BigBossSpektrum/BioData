document.addEventListener('DOMContentLoaded', function () {
    const inputTexto = document.getElementById('filtroUsuarios');
    const inputDesde = document.getElementById('filtroDesde');
    const inputHasta = document.getElementById('filtroHasta');
    const selectEstado = document.getElementById('filtroEstado');
    const filas = Array.from(document.querySelectorAll('tbody tr')).filter(f => !f.id);
    const sinCoincidencias = document.getElementById('sinCoincidencias');

    function aplicarFiltros() {
        const texto = inputTexto.value.toLowerCase();
        const desde = inputDesde.value;
        const hasta = inputHasta.value;
        const estadoFiltro = selectEstado ? selectEstado.value : '';
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

            // Filtro por estado de aprobación
            if (estadoFiltro && visible) {
                const celdaAprobado = fila.cells[10]; // Columna "Aprobado" (índice 10)
                const textoAprobado = celdaAprobado ? celdaAprobado.textContent.toLowerCase().trim() : '';
                
                let cumpleEstado = false;
                
                switch (estadoFiltro) {
                    case 'aprobado':
                        cumpleEstado = textoAprobado.includes('aprobado');
                        break;
                    case 'rechazado':
                        cumpleEstado = textoAprobado.includes('rechazado');
                        break;
                    case 'pendiente':
                        cumpleEstado = textoAprobado.includes('pendiente') || 
                                     (celdaAprobado && (celdaAprobado.querySelector('.btn-confirmar-aprobacion') || celdaAprobado.querySelector('.btn-confirmar-rechazo')));
                        break;
                    case 'sin_horas_extra':
                        cumpleEstado = textoAprobado === '-' || textoAprobado === '';
                        break;
                }
                
                if (!cumpleEstado) {
                    visible = false;
                }
            }

            fila.style.display = visible ? '' : 'none';
            if (visible) visibles++;
        });

        sinCoincidencias.style.display = visibles === 0 ? '' : 'none';
        
        // Actualizar resumen total después de aplicar filtros
        if (typeof calcularResumenTotal === 'function') {
            calcularResumenTotal();
        }
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
        
        if (selectEstado && selectEstado.value) {
            params.set('estado', selectEstado.value);
        } else {
            params.delete('estado');
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
    if (selectEstado) {
        selectEstado.addEventListener('change', aplicarFiltros);
    }

    // Aplicar filtros con paginación después de un breve delay para evitar múltiples recargas
    let timeoutId;
    inputTexto.addEventListener('input', function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(aplicarFiltrosConPaginacion, 1000); // 1 segundo de delay
    });

    inputDesde.addEventListener('change', aplicarFiltrosConPaginacion);
    inputHasta.addEventListener('change', aplicarFiltrosConPaginacion);
    if (selectEstado) {
        selectEstado.addEventListener('change', aplicarFiltrosConPaginacion);
    }

    // Aplicar filtros iniciales
    aplicarFiltros();
});
