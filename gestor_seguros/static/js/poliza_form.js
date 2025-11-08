// static/js/poliza_form.js (Versión de Depuración Definitiva)
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log("SCRIPT DE FORMULARIO DE PÓLIZA CARGADO Y LISTO.");

        const addButton = document.getElementById('add-asegurado-form');
        const container = document.getElementById('asegurado-forms-container');
        const totalFormsInput = document.querySelector('input[name="asegurados-TOTAL_FORMS"]');
        const emptyFormTemplate = document.getElementById('empty-form-template');
        const noAseguradosMessage = document.getElementById('no-asegurados-message');

        if (!addButton) {
            console.error("ERROR CRÍTICO: No se encontró el botón con id='add-asegurado-form'. El script no puede continuar.");
            return;
        }
        
        console.log("Botón 'Añadir Asegurado' encontrado. Añadiendo listener de clic...");

        addButton.addEventListener('click', function() {
            try {
                console.log("¡CLIC DETECTADO! Intentando añadir un nuevo formulario.");

                // 1. Ocultar el mensaje de "no hay asegurados"
                if (noAseguradosMessage) {
                    noAseguradosMessage.style.display = 'none';
                } else {
                    console.warn("Advertencia: No se encontró el elemento 'no-asegurados-message'.");
                }

                // 2. Comprobar que los elementos necesarios existen ANTES de usarlos
                if (!container || !totalFormsInput || !emptyFormTemplate) {
                    console.error("ERROR DENTRO DEL CLIC: Faltan elementos esenciales del formset.");
                    console.log({ container, totalFormsInput, emptyFormTemplate });
                    return;
                }

                // 3. Obtener el número de formulario
                let formNum = parseInt(totalFormsInput.value);
                console.log(`Número total de formularios actual: ${formNum}`);

                // 4. Clonar la plantilla y reemplazar el prefijo
                let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formNum);
                console.log("HTML del nuevo formulario generado.");

                // 5. Añadir el nuevo formulario al contenedor
                container.insertAdjacentHTML('beforeend', newFormHtml);
                console.log("Nuevo formulario añadido al DOM.");

                // 6. Incrementar el contador total de formularios
                totalFormsInput.value = formNum + 1;
                console.log(`Nuevo número total de formularios: ${totalFormsInput.value}`);

            } catch (error) {
                // Si algo falla, lo veremos aquí
                console.error("¡ERROR CATASTRÓFICO DURANTE EL CLIC!", error);
                alert("Ocurrió un error de JavaScript. Por favor, revisa la consola del navegador.");
            }
        });
        
        console.log("Listener de clic añadido exitosamente.");

        // El resto del código para el efecto visual de 'Eliminar'
        if (container) {
            container.addEventListener('click', function(e) {
                // ... (código para eliminar y para el efecto visual)
            });
        }
    });
})();