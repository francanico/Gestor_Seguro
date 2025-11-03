(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log("poliza_form.js cargado."); // Depuración: Verifica que el archivo se carga

        const addButton = document.getElementById('add-asegurado-form');
        const container = document.getElementById('asegurado-forms-container');
        const totalFormsInput = document.getElementById('id_asegurados-TOTAL_FORMS');
        const emptyFormTemplate = document.getElementById('empty-form-template');
        const noAseguradosMessage = document.getElementById('no-asegurados-message');

        // Depuración: Verifica que todos los elementos HTML necesarios existen
        if (!addButton || !container || !totalFormsInput || !emptyFormTemplate) {
            console.error('Error Crítico: Faltan uno o más elementos esenciales del formset en el HTML.');
            console.log({
                addButton,
                container,
                totalFormsInput,
                emptyFormTemplate
            });
            return; // Detiene el script si algo falta
        }

        addButton.addEventListener('click', function() {
            console.log("Botón 'Añadir Asegurado' presionado."); // Depuración

            if (noAseguradosMessage) {
                noAseguradosMessage.style.display = 'none';
            }

            let formNum = parseInt(totalFormsInput.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formNum);
            
            container.insertAdjacentHTML('beforeend', newFormHtml);
            totalFormsInput.value = formNum + 1;
        });

        container.addEventListener('click', function(e) {
            // Manejar el botón de cerrar 'x' en formularios nuevos
            if (e.target && e.target.classList.contains('remove-asegurado-form')) {
                e.target.closest('.asegurado-form').remove();
                
                if (container.children.length === 0 && noAseguradosMessage) {
                    noAseguradosMessage.style.display = 'block';
                }
            }
            
            // Manejar el checkbox 'Eliminar' en formularios existentes
            if (e.target && e.target.getAttribute('name') && e.target.getAttribute('name').endsWith('-DELETE')) {
                const formElement = e.target.closest('.asegurado-form');
                if (e.target.checked) {
                    formElement.style.opacity = '0.5';
                    formElement.style.backgroundColor = '#ffebee';
                } else {
                    formElement.style.opacity = '1';
                    formElement.style.backgroundColor = 'transparent';
                }
            }
        });
    });
})();