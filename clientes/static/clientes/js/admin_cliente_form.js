// static/clientes/js/admin_cliente_form.js
window.addEventListener("load", function() {
    (function($) {
        function toggleFields() {
            var tipoPessoa = $("#id_tipo_pessoa").val();
            if (tipoPessoa === 'PF') {
                $('.pj-fields').hide();
                $('.pf-fields').show();
            } else {
                $('.pf-fields').hide();
                $('.pj-fields').show();
            }
        }
        // Quando a página carregar
        toggleFields();
        // Quando o campo mudar
        $("#id_tipo_pessoa").change(function() {
            toggleFields();
        });
    })(django.jQuery);
});