(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log("reportes.js cargado.");

        // --- Gráfico de Producción ---
        try {
            const produccionData = JSON.parse(document.getElementById('produccion-data').textContent);
            if (produccionData.length > 0) {
                const ctx = document.getElementById('produccionChart').getContext('2d');
                const labels = produccionData.map(item => new Date(item.mes).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }));
                const data = produccionData.map(item => item.total_prima);
                new Chart(ctx, { type: 'bar', data: { labels: labels, datasets: [{ label: 'Prima Emitida', data: data, backgroundColor: 'rgba(59, 113, 202, 0.7)' }] } });
            }
        } catch (e) { console.error('Error en gráfico de producción:', e); }

        // --- Gráfico de Cartera por Ramo ---
        try {
            const carteraRamoData = JSON.parse(document.getElementById('cartera-ramo-data').textContent);
            if (carteraRamoData.length > 0) {
                const ctx = document.getElementById('carteraRamoChart').getContext('2d');
                const labels = carteraRamoData.map(item => item.ramo_tipo_seguro);
                const data = carteraRamoData.map(item => item.cantidad);
                new Chart(ctx, { type: 'doughnut', data: { labels: labels, datasets: [{ data: data, backgroundColor: ['#3B71CA', '#198754', '#ffc107', '#dc3545', '#0dcaf0'] }] } });
            }
        } catch (e) { console.error('Error en gráfico de cartera por ramo:', e); }

        // --- Gráfico de Cartera por Aseguradora ---
        try {
            const carteraAseguradoraData = JSON.parse(document.getElementById('cartera-aseguradora-data').textContent);
            if (carteraAseguradoraData.length > 0) {
                const ctx = document.getElementById('carteraAseguradoraChart').getContext('2d');
                const labels = carteraAseguradoraData.map(item => item.nombre_aseguradora);
                const data = carteraAseguradoraData.map(item => item.cantidad);
                new Chart(ctx, { type: 'pie', data: { labels: labels, datasets: [{ data: data, backgroundColor: ['#6f42c1', '#fd7e14', '#20c997', '#6610f2', '#e83e8c'] }] } });
            }
        } catch (e) { console.error('Error en gráfico de cartera por aseguradora:', e); }
    });
})();