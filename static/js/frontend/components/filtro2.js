document.addEventListener('DOMContentLoaded', function () {
    // Funciones helper para el spinner de carga (en caso de que no estén definidas globalmente)
    function safeMostrarCargando() {
        if (typeof mostrarCargando === 'function') {
            mostrarCargando();
        }
    }
    
    function safeMostrarCargandoTemporal(duracion = 300) {
        if (typeof mostrarCargandoTemporal === 'function') {
            mostrarCargandoTemporal(duracion);
        }
    }
    
    const inputTexto = document.getElementById('filtroUsuarios');
    const inputDesde = document.getElementById('filtroDesde');
    const inputHasta = document.getElementById('filtroHasta');
    const selectEstado = document.getElementById('filtroEstado');
    const filas = Array.from(document.querySelectorAll('tbody tr')).filter(f => !f.id);
    const sinCoincidencias = document.getElementById('sinCoincidencias');

    // Agregar focus al filtro de usuarios al cargar la página
    if (inputTexto) {
        setTimeout(() => {
            inputTexto.focus();
            // Posicionar el cursor al final del texto existente
            if (inputTexto.value) {
                inputTexto.setSelectionRange(inputTexto.value.length, inputTexto.value.length);
            }
        }, 100); // Pequeño delay para asegurar que la página esté completamente cargada
    }

    // Verificar si hay filtros aplicados desde el backend
    function hayFiltrosAplicados() {
        const urlParams = new URLSearchParams(window.location.search);
        const filtrosBackend = ['nombre', 'estacion', 'fecha_inicio', 'fecha_fin', 'search', 'fecha_desde', 'fecha_hasta', 'estado'];
        
        // Verificar filtros de URL
        for (let filtro of filtrosBackend) {
            if (urlParams.get(filtro) && urlParams.get(filtro).trim() !== '') {
                return true;
            }
        }
        
        // Verificar filtros de formulario
        if (inputTexto && inputTexto.value.trim() !== '') return true;
        if (inputDesde && inputDesde.value.trim() !== '') return true;
        if (inputHasta && inputHasta.value.trim() !== '') return true;
        if (selectEstado && selectEstado.value.trim() !== '') return true;
        
        return false;
    }

    // Mostrar/ocultar contenido basado en filtros
    function toggleContenidoPorFiltros() {
        const hayFiltros = hayFiltrosAplicados();
        const mensajeSinFiltros = document.getElementById('mensaje-sin-filtros');
        const tablaDatos = document.getElementById('tabla-datos');
        const resumenTotal = document.getElementById('resumen-total');
        const resumenRetrasos = document.getElementById('resumen-retrasos');
        
        if (hayFiltros) {
            // Mostrar datos y ocultar mensaje
            if (mensajeSinFiltros) mensajeSinFiltros.style.display = 'none';
            if (tablaDatos) tablaDatos.style.display = 'block';
        } else {
            // Ocultar datos y mostrar mensaje (si existe)
            if (mensajeSinFiltros) mensajeSinFiltros.style.display = 'block';
            if (tablaDatos) tablaDatos.style.display = 'none';
            if (resumenTotal) resumenTotal.style.display = 'none';
            if (resumenRetrasos) resumenRetrasos.style.display = 'none';
        }
    }

    function aplicarFiltros() {
        // Mostrar indicador de carga temporal para filtros locales
        safeMostrarCargandoTemporal(300);
        
        // Verificar estado de filtros primero
        toggleContenidoPorFiltros();
        
        // Si no hay filtros aplicados, no procesar la tabla
        if (!hayFiltrosAplicados()) {
            return;
        }

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
        
        // Actualizar estado de contenido por filtros
        toggleContenidoPorFiltros();
        
        // Actualizar resumen total después de aplicar filtros
        if (typeof window.calcularResumenTotal === 'function') {
            console.log('🔄 Llamando a calcularResumenTotal desde filtro...');
            window.calcularResumenTotal();
        } else if (typeof calcularResumenTotal === 'function') {
            console.log('🔄 Llamando a calcularResumenTotal (referencia local) desde filtro...');
            calcularResumenTotal();
        } else {
            console.warn('⚠️ calcularResumenTotal no está disponible');
        }
    }

    // Función para actualizar URL con filtros y recargar la página
    function aplicarFiltrosConPaginacion() {
        // Mostrar indicador de carga justo antes de navegar
        safeMostrarCargando();
        
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
    inputTexto.addEventListener('input', function() {
        aplicarFiltros();
        toggleContenidoPorFiltros();
    });
    inputDesde.addEventListener('change', function() {
        aplicarFiltros();
        toggleContenidoPorFiltros();
    });
    inputHasta.addEventListener('change', function() {
        aplicarFiltros();
        toggleContenidoPorFiltros();
    });
    if (selectEstado) {
        selectEstado.addEventListener('change', function() {
            aplicarFiltros();
            toggleContenidoPorFiltros();
        });
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
    toggleContenidoPorFiltros(); // Verificar estado inicial
    aplicarFiltros();
});
