$(document).ready(function() {
    $('input[type=radio]').click(function() {
        $(this).closest("form").submit();
    });
    $('#reveal_form').click(function() {
        $('.add_event').show();
        $(this).hide();
    });
});
