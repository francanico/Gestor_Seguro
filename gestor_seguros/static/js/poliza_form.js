(function() {
    console.log("INTENTANDO INICIAR SCRIPT: poliza_form.js");

    document.addEventListener('DOMContentLoaded', function() {
        console.log("EVENTO DOMContentLoaded DISPARADO.");

        const addButton = document.getElementById('add-asegurado-form');
        const container = document.getElementById('asegurado-forms-container');
        const totalFormsInput = document.querySelector('input[name="asegurados-TOTAL_FORMS"]');
        const emptyFormTemplate = document.getElementById('empty-form-template');
        const noAseguradosMessage = document.getElementById('no-asegurados-message');

        console.log("Buscando elementos...");
        console.log("Botón 'Añadir':", addButton);
        console.log("Contenedor:", container);
        console.log("Input Total Forms:", totalFormsInput);
        console.log("Plantilla:", emptyFormTemplate);

        if (!addButton) {
            console.error("ERROR CRÍTICO: No se encontró el botón con id='add-asegurado-form'.");
            return;
        }

        if (!container || !totalFormsInput || !emptyFormTemplate) {
            console.error("ERROR CRÍTICO: Faltan elementos esenciales del formset.");
            return;
        }
        
        console.log("Todos los elementos encontrados. Añadiendo listener al botón.");
        
        addButton.addEventListener('click', function() {
            console.log("¡CLIC DETECTADO! Añadiendo nuevo formulario.");

            if (noAseguradosMessage) {
                noAseguradosMessage.style.display = 'none';
            }
            
            let formNum = parseInt(totalFormsInput.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formNum);
            
            container.insertAdjacentHTML('beforeend', newFormHtml);
            totalFormsInput.value = formNum + 1;
        });
        
        console.log("Listener añadido exitosamente al botón 'Añadir Asegurado'.");

        // ... (el resto del script para eliminar)
    });
})();