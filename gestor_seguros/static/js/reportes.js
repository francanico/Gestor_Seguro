(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log("reportes.js cargado.");

        // --- Gráfico de Producción ---
        try {
            const produccionData = JSON.parse(document.getElementById('produccion-data').textContent);
            if (produccionData.length > 0) {
                const ctx = document.getElementById('produccionChart');
                // ... (código del gráfico de producción sin cambios)
            }
        } catch (e) { console.error('Error en gráfico de producción:', e); }

        // --- Gráfico de Cartera por Ramo ---
        try {
            const carteraRamoData = JSON.parse(document.getElementById('cartera-ramo-data').textContent);
            if (carteraRamoData.length > 0) {
                const ctx = document.getElementById('carteraRamoChart');
                const labels = carteraRamoData.map(item => item.ramo_tipo_seguro);
                const data = carteraRamoData.map(item => item.cantidad);
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{ data: data, /* ... colores ... */ }]
                    }
                });
            }
        } catch (e) { console.error('Error en gráfico de cartera por ramo:', e); }

        // --- Gráfico de Cartera por Aseguradora ---
        try {
            const carteraAseguradoraData = JSON.parse(document.getElementById('cartera-aseguradora-data').textContent);
            if (carteraAseguradoraData.length > 0) {
                const ctx = document.getElementById('carteraAseguradoraChart');
                const labels = carteraAseguradoraData.map(item => item.nombre_aseguradora);
                const data = carteraAseguradoraData.map(item => item.cantidad);
                new Chart(ctx, {
                    type: 'pie', // Usamos 'pie' para variar
                    data: {
                        labels: labels,
                        datasets: [{ data: data, /* ... colores ... */ }]
                    }
                });
            }
        } catch (e) { console.error('Error en gráfico de cartera por aseguradora:', e); }
    });
})();