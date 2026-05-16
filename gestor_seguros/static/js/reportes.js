(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log("reportes.js cargado.");

        // Paleta de colores compartida
        const COLORS = [
            '#6f42c1', '#fd7e14', '#20c997', '#3B71CA', '#dc3545',
            '#198754', '#ffc107', '#0dcaf0', '#e83e8c', '#6610f2'
        ];

        // Formatea números como moneda abreviada (ej: 12,500 → 12.5K)
        function formatPrima(value) {
            if (value == null) return '$0';
            if (value >= 1_000_000) return '$' + (value / 1_000_000).toFixed(1) + 'M';
            if (value >= 1_000)     return '$' + (value / 1_000).toFixed(1) + 'K';
            return '$' + value.toFixed(2);
        }

        // Plugin de tooltip personalizado para mostrar ambos datasets
        const tooltipPlugin = {
            callbacks: {
                label: function(context) {
                    const label = context.dataset.label || '';
                    const value = context.parsed.y ?? context.parsed;
                    if (label.includes('Prima')) {
                        return ` ${label}: ${formatPrima(value)}`;
                    }
                    return ` ${label}: ${value} póliza${value !== 1 ? 's' : ''}`;
                }
            }
        };

        // Opciones comunes para gráficos de barras dobles
        function barOptions(yLeftLabel, yRightLabel) {
            return {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: tooltipPlugin
                },
                scales: {
                    x: { ticks: { maxRotation: 35, minRotation: 0 } },
                    yPolizas: {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: yLeftLabel },
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    yPrima: {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: yRightLabel },
                        beginAtZero: true,
                        grid: { drawOnChartArea: false },
                        ticks: {
                            callback: function(val) { return formatPrima(val); }
                        }
                    }
                }
            };
        }

        // --- Gráfico de Producción por Mes ---
        try {
            const produccionData = JSON.parse(document.getElementById('produccion-data').textContent);
            if (produccionData.length > 0) {
                const ctx = document.getElementById('produccionChart').getContext('2d');
                const labels = produccionData.map(item =>
                    new Date(item.mes).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' })
                );
                const data = produccionData.map(item => item.total_prima);
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Prima Emitida',
                            data: data,
                            backgroundColor: 'rgba(59, 113, 202, 0.7)'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { tooltip: tooltipPlugin }
                    }
                });
            }
        } catch (e) { console.error('Error en gráfico de producción:', e); }


        // --- Gráfico de Cartera por Ramo (Barras dobles) ---
        try {
            const carteraRamoData = JSON.parse(document.getElementById('cartera-ramo-data').textContent);
            if (carteraRamoData.length > 0) {
                const ctx = document.getElementById('carteraRamoChart').getContext('2d');
                const labels   = carteraRamoData.map(item => item.ramo_tipo_seguro);
                const cantidad = carteraRamoData.map(item => item.cantidad);
                const primas   = carteraRamoData.map(item => item.total_prima || 0);
                const bgColors = labels.map((_, i) => COLORS[i % COLORS.length]);

                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Pólizas',
                                data: cantidad,
                                backgroundColor: bgColors.map(c => c + 'CC'),
                                borderColor: bgColors,
                                borderWidth: 1.5,
                                yAxisID: 'yPolizas',
                                order: 2
                            },
                            {
                                label: 'Prima Total',
                                data: primas,
                                type: 'line',
                                backgroundColor: 'rgba(253,126,20,0.15)',
                                borderColor: '#fd7e14',
                                borderWidth: 2.5,
                                pointBackgroundColor: '#fd7e14',
                                pointRadius: 5,
                                fill: true,
                                tension: 0.3,
                                yAxisID: 'yPrima',
                                order: 1
                            }
                        ]
                    },
                    options: barOptions('Cantidad de Pólizas', 'Prima Total ($)')
                });
            }
        } catch (e) { console.error('Error en gráfico de cartera por ramo:', e); }


        // --- Gráfico de Cartera por Aseguradora (Barras dobles) ---
        try {
            const carteraAseguradoraData = JSON.parse(document.getElementById('cartera-aseguradora-data').textContent);
            if (carteraAseguradoraData.length > 0) {
                const ctx = document.getElementById('carteraAseguradoraChart').getContext('2d');
                const labels   = carteraAseguradoraData.map(item => item.nombre_aseguradora || 'Sin aseguradora');
                const cantidad = carteraAseguradoraData.map(item => item.cantidad);
                const primas   = carteraAseguradoraData.map(item => item.total_prima || 0);
                const bgColors = labels.map((_, i) => COLORS[i % COLORS.length]);

                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Pólizas',
                                data: cantidad,
                                backgroundColor: bgColors.map(c => c + 'CC'),
                                borderColor: bgColors,
                                borderWidth: 1.5,
                                yAxisID: 'yPolizas',
                                order: 2
                            },
                            {
                                label: 'Prima Total',
                                data: primas,
                                type: 'line',
                                backgroundColor: 'rgba(32,201,151,0.15)',
                                borderColor: '#20c997',
                                borderWidth: 2.5,
                                pointBackgroundColor: '#20c997',
                                pointRadius: 5,
                                fill: true,
                                tension: 0.3,
                                yAxisID: 'yPrima',
                                order: 1
                            }
                        ]
                    },
                    options: barOptions('Cantidad de Pólizas', 'Prima Total ($)')
                });
            }
        } catch (e) { console.error('Error en gráfico de cartera por aseguradora:', e); }

    });
})();