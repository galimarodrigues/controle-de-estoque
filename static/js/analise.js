document.addEventListener('DOMContentLoaded', function () {
    const dadosElement = document.getElementById('pontos-clusters-data');
    const canvas = document.getElementById('clusterChart');

    if (!dadosElement || !canvas) {
        return;
    }

    if (typeof Chart === 'undefined') {
        console.error('Chart.js não foi carregado.');
        return;
    }

    let pontosClusters;

    try {
        pontosClusters = JSON.parse(dadosElement.textContent);
    } catch (error) {
        console.error('Não foi possível interpretar os dados dos clusters.', error);
        return;
    }

    if (!Array.isArray(pontosClusters)) {
        console.error('Os dados dos clusters não estão no formato esperado.', pontosClusters);
        return;
    }

    const datasets = pontosClusters.map(function (grupo) {
        return {
            label: 'Cluster ' + grupo.cluster + ' — ' + grupo.nome,
            data: (grupo.pontos || []).map(function (ponto) {
                return {
                    x: Number(ponto.x),
                    y: Number(ponto.y),
                    produto: ponto.produto
                };
            }),
            pointRadius: 6,
            pointHoverRadius: 9
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
            interaction: {
                mode: 'nearest',
                intersect: true
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const ponto = context.raw;
                            return ponto.produto + ' — ' + context.dataset.label;
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

    function iniciarVLibras() {
        if (window.VLibras && typeof window.VLibras.Widget === 'function') {
            new window.VLibras.Widget('https://vlibras.gov.br/app');
            return true;
        }
        return false;
    }

    if (!iniciarVLibras()) {
        window.addEventListener('load', iniciarVLibras, { once: true });
    }
});
