// Usamos una función anónima para evitar conflictos con otras variables globales
(function() {
    // Esperamos a que todo el contenido del DOM esté cargado
    document.addEventListener('DOMContentLoaded', function() {

        console.log("reportes.js cargado y ejecutándose."); // Mensaje de depuración

        // --- Gráfico de Producción por Mes (Barras) ---
        try {
            const produccionDataEl = document.getElementById('produccion-data');
            if (produccionDataEl) {
                const produccionData = JSON.parse(produccionDataEl.textContent);
                console.log("Datos de Producción:", produccionData); // Depuración

                if (produccionData.length > 0) {
                    const produccionCtx = document.getElementById('produccionChart');
                    const produccionLabels = produccionData.map(item => 
                        new Date(item.mes).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' })
                    );
                    const produccionValues = produccionData.map(item => item.total_prima);
                    
                    new Chart(produccionCtx, {
                        type: 'bar',
                        data: {
                            labels: produccionLabels,
                            datasets: [{
                                label: 'Prima Emitida',
                                data: produccionValues,
                                backgroundColor: 'rgba(59, 113, 202, 0.7)',
                                borderColor: 'rgba(59, 113, 202, 1)',
                                borderRadius: 4,
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: { y: { beginAtZero: true } },
                            plugins: { 
                                tooltip: { 
                                    callbacks: { 
                                        label: context => '$' + parseFloat(context.parsed.y).toLocaleString('es-VE', {minimumFractionDigits: 2, maximumFractionDigits: 2})
                                    } 
                                } 
                            }
                        }
                    });
                }
            } else {
                console.log("Elemento 'produccion-data' no encontrado.");
            }
        } catch (e) {
            console.error('Error al procesar el gráfico de producción:', e);
        }

        // --- Gráfico de Cartera por Ramo (Dona) ---
        try {
            const carteraDataEl = document.getElementById('cartera-data');
            if (carteraDataEl) {
                const carteraData = JSON.parse(carteraDataEl.textContent);
                console.log("Datos de Cartera:", carteraData); // Depuración

                if (carteraData.length > 0) {
                    const carteraCtx = document.getElementById('carteraChart');
                    const carteraLabels = carteraData.map(item => item.ramo_tipo_seguro);
                    const carteraValues = carteraData.map(item => item.cantidad);

                    new Chart(carteraCtx, {
                        type: 'doughnut',
                        data: {
                            labels: carteraLabels,
                            datasets: [{
                                label: '# de Pólizas',
                                data: carteraValues,
                                backgroundColor: ['#3B71CA', '#198754', '#ffc107', '#dc3545', '#0dcaf0', '#6f42c1'],
                                hoverOffset: 4
                            }]
                        }
                    });
                }
            } else {
                console.log("Elemento 'cartera-data' no encontrado.");
            }
        } catch (e) {
            console.error('Error al procesar el gráfico de cartera:', e);
        }

        // NUEVO CÓDIGO PARA EL GRÁFICO DE ASEGURADORAS
        // ====================================================
        try {
            const aseguradoraDataEl = document.getElementById('aseguradora-data');
            if (aseguradoraDataEl) {
                const aseguradoraData = JSON.parse(aseguradoraDataEl.textContent);
                console.log("Datos por Aseguradora:", aseguradoraData);

                if (aseguradoraData.length > 0) {
                    const aseguradoraCtx = document.getElementById('aseguradoraChart');
                    const aseguradoraLabels = aseguradoraData.map(item => item.aseguradora__nombre);
                    const aseguradoraValues = aseguradoraData.map(item => item.total_prima);

                    new Chart(aseguradoraCtx, {
                        type: 'pie', // Usamos un gráfico de pie, que es bueno para esto
                        data: {
                            labels: aseguradoraLabels,
                            datasets: [{
                                label: 'Producción por Aseguradora',
                                data: aseguradoraValues,
                                backgroundColor: [
                                    '#0d6efd', '#6610f2', '#6f42c1', 
                                    '#d63384', '#dc3545', '#fd7e14', '#ffc107'
                                ],
                                hoverOffset: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    position: 'top',
                                }
                            }
                        }
                    });
                }
            }
        } catch (e) {
            console.error('Error al renderizar el gráfico por aseguradora:', e);
        }

    });
})();