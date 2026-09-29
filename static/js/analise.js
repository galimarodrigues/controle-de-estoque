document.addEventListener('DOMContentLoaded', function () {
    const dadosElement = document.getElementById('pontos-clusters-data');
    const canvas = document.getElementById('clusterChart');

    if (dadosElement && canvas && typeof Chart !== 'undefined') {
        const pontosClusters = JSON.parse(dadosElement.textContent);

        const datasets = pontosClusters.map(function (grupo) {
            return {
                label: 'Cluster ' + grupo.cluster + ' — ' + grupo.nome,
                data: grupo.pontos.map(function (ponto) {
                    return {
                        x: ponto.x,
                        y: ponto.y,
                        produto: ponto.produto
                    };
                }),
                pointRadius: 7,
                pointHoverRadius: 10
            };
        });

        new Chart(canvas.getContext('2d'), {
            type: 'scatter',
            data: {
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return context.raw.produto + ' — ' + context.dataset.label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'PCA 1'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'PCA 2'
                        }
                    }
                }
            }
        });
    }

    if (window.VLibras && typeof window.VLibras.Widget === 'function') {
        new window.VLibras.Widget('https://vlibras.gov.br/app');
    }
});
