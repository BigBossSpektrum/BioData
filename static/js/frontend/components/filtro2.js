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
                // Convertir fechas a strings YYYY-MM-DD para comparación directa
                const fechaStr = fechaTexto; // Ya debería estar en formato YYYY-MM-DD
                const desdeStr = desde || '';
                const hastaStr = hasta || '';

                if (desdeStr && fechaStr < desdeStr) visible = false;
                if (hastaStr && fechaStr > hastaStr) visible = false;
            } else if (desde || hasta) {
                // Si hay filtro de fecha pero la fila no tiene fecha, ocultar fila
                visible = false;
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

    // Función para aplicar filtros con paginación (buscar)
    function buscarFiltros() {
        // Mostrar indicador de carga justo antes de navegar
        safeMostrarCargando();
        
        const params = new URLSearchParams(window.location.search);
        
        // Limpiar parámetros existentes de filtros de búsqueda
        params.delete('search');
        params.delete('fecha_desde');
        params.delete('fecha_hasta');
        params.delete('estado');
        
        // Agregar los nuevos filtros de búsqueda solo si tienen valor
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

    // Función para limpiar filtros
    function limpiarFiltros() {
        safeMostrarCargando();
        // Redirigir a la página sin parámetros de filtro
        window.location.href = window.location.pathname;
    }

    // Configurar event listeners para búsqueda solo con Enter
    if (inputTexto) {
        inputTexto.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                buscarFiltros();
            }
        });
    }

    if (inputDesde) {
        inputDesde.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                buscarFiltros();
            }
        });
    }

    if (inputHasta) {
        inputHasta.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                buscarFiltros();
            }
        });
    }

    // Hacer las funciones disponibles globalmente para el HTML
    window.buscarFiltros = buscarFiltros;
    window.limpiarFiltros = limpiarFiltros;

    // Aplicar filtros iniciales
    toggleContenidoPorFiltros(); // Verificar estado inicial
    aplicarFiltros();
});
