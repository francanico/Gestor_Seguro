(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const addButton = document.getElementById('add-asegurado-form');
        const container = document.getElementById('asegurado-forms-container');
        const totalFormsInput = document.querySelector('input[name="asegurados-TOTAL_FORMS"]');
        const emptyFormTemplate = document.getElementById('empty-form-template');
        const noAseguradosMessage = document.getElementById('no-asegurados-message');

        if (!addButton || !container || !totalFormsInput || !emptyFormTemplate) {
            console.error("Faltan elementos del formset en el DOM. El script de añadir/quitar no funcionará.");
            return;
        }

        addButton.addEventListener('click', function() {
            if (noAseguradosMessage) {
                noAseguradosMessage.style.display = 'none';
            }
            
            let formNum = parseInt(totalFormsInput.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formNum);
            
            container.insertAdjacentHTML('beforeend', newFormHtml);
            totalFormsInput.value = formNum + 1;
        });

        container.addEventListener('click', function(e) {
            // Manejar botón de cerrar 'x' en formularios nuevos
            if (e.target && e.target.classList.contains('remove-asegurado-form')) {
                e.target.closest('.asegurado-form').remove();
                if (container.children.length === 0 && noAseguradosMessage) {
                    noAseguradosMessage.style.display = 'block';
                }
            }
            
            // Manejar checkbox 'Eliminar' para efecto visual
            if (e.target && e.target.getAttribute('name') && e.target.getAttribute('name').endsWith('-DELETE')) {
                const formElement = e.target.closest('.asegurado-form');
                if (e.target.checked) {
                    formElement.style.opacity = '0.5';
                } else {
                    formElement.style.opacity = '1';
                }
            }
        });
    });
})();