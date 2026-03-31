window.addEventListener('DOMContentLoaded', event => {
    ['datatablesSimple', 'datatablesMovimentacoes', 'datatablesMovimentacoesRecentes'].forEach((tableId) => {
        const table = document.getElementById(tableId);
        if (table) {
            new simpleDatatables.DataTable(table);
        }
    });
});
