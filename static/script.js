$(document).ready(function() {
    $('input[type=radio]').click(function() {
        $(this).closest("form").submit();
    });
});
