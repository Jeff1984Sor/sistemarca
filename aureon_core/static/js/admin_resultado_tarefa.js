// static/js/admin_resultado_tarefa.js

(function($) {
    $(document).ready(function() {
        var acaoSelect = $('#id_acao');
        
        function toggleConditionalFields() {
            var selectedAction = acaoSelect.val();
            
            // Esconde todos os grupos de ações condicionais
            $('.azione-ir-para-fase').hide();
            $('.azione-aguardar-dias').hide();
            $('.azione-criar-tarefa').hide();
            
            // Mostra o grupo correto com base na ação selecionada
            if (selectedAction === 'IR_PARA_FASE') {
                $('.azione-ir-para-fase').show();
            } else if (selectedAction === 'AGUARDAR_DIAS') {
                $('.azione-aguardar-dias').show();
            } else if (selectedAction === 'CRIAR_TAREFA') {
                $('.azione-criar-tarefa').show();
            }
        }
        
        // Executa a função quando a página carrega
        toggleConditionalFields();
        
        // Executa a função toda vez que o valor do select 'Acao' muda
        acaoSelect.on('change', function() {
            toggleConditionalFields();
        });
    });
})(django.jQuery);