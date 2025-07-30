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

    inputTexto.addEventListener('input', aplicarFiltros);
    inputDesde.addEventListener('change', aplicarFiltros);
    inputHasta.addEventListener('change', aplicarFiltros);
});
