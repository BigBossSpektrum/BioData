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
            // Solo la fecha (YYYY-MM-DD) de la columna entrada
            const fechaTexto = fila.querySelector('.col-dia').textContent.trim().slice(0,10);

            let visible = true;

            // Filtro de texto
            if (texto && !textoFila.includes(texto)) {
                visible = false;
            }

            // Filtro por fecha desde: igual o mayor
            if (desde && fechaTexto < desde) {
                visible = false;
            }

            // Filtro por fecha hasta: menor o igual
            if (hasta && fechaTexto > hasta) {
                visible = false;
            }

            fila.style.display = visible ? '' : 'none';
            if (visible) visibles++;
        });

        sinCoincidencias.style.display = visibles === 0 ? '' : 'none';
    }

    // Función para actualizar URL con filtros y recargar la página
    function aplicarFiltrosConPaginacion() {
        const params = new URLSearchParams();
        
        if (inputTexto.value.trim()) {
            params.set('search', inputTexto.value.trim());
        }
        if (inputDesde.value) {
            params.set('fecha_desde', inputDesde.value);
        }
        if (inputHasta.value) {
            params.set('fecha_hasta', inputHasta.value);
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