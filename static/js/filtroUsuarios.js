// Filtro de usuarios reutilizable para cualquier página con input#filtroUsuarios
// Llama window.filtroUsuariosInit() después de cargar el DOM o con defer
window.filtroUsuariosInit = function() {
    var input = document.getElementById('filtroUsuarios');
    if (!input) return;
    var next = input.parentElement;
    var table = null;
    while (next && !table) {
        next = next.nextElementSibling;
        if (next && next.tagName && next.tagName.toLowerCase() === 'table') {
            table = next;
        }
    }
    if (!table) {
        table = document.querySelector('table');
    }
    if (!table) return;
    var tbody = table.querySelector('tbody');
    if (!tbody) return;
    input.addEventListener('input', function() {
        var filter = input.value.toLowerCase();
        Array.from(tbody.rows).forEach(function(row) {
            var text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
};

