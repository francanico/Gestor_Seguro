// static/js/poliza_form.js

function addAseguradoForm() {
    console.log("Función addAseguradoForm() llamada."); // Depuración

    const container = document.getElementById('asegurado-forms-container');
    const totalFormsInput = document.querySelector('input[name="asegurados-TOTAL_FORMS"]');
    const emptyFormTemplate = document.getElementById('empty-form-template');
    const noAseguradosMessage = document.getElementById('no-asegurados-message');

    if (!container || !totalFormsInput || !emptyFormTemplate) {
        console.error("Error: Faltan elementos del formset en el DOM.");
        return;
    }

    if (noAseguradosMessage) {
        noAseguradosMessage.style.display = 'none';
    }

    let formNum = parseInt(totalFormsInput.value);
    let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formNum);
    
    container.insertAdjacentHTML('beforeend', newFormHtml);
    totalFormsInput.value = formNum + 1;
}

// El listener para el efecto de 'Eliminar' se mantiene igual,
// ya que sabemos que esa parte funciona.
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('asegurado-forms-container');
    if (container) {
        container.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('remove-asegurado-form')) {
                e.target.closest('.asegurado-form').remove();
                if (container.children.length === 0 && document.getElementById('no-asegurados-message')) {
                    document.getElementById('no-asegurados-message').style.display = 'block';
                }
            }
            
            if (e.target && e.target.getAttribute('name') && e.target.getAttribute('name').endsWith('-DELETE')) {
                const formElement = e.target.closest('.asegurado-form');
                if (e.target.checked) {
                    formElement.style.opacity = '0.5';
                } else {
                    formElement.style.opacity = '1';
                }
            }
        });
    }
});