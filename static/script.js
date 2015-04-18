var applyPanelClass = function() {
    var date, currentDate, startTime, endTime;
    date = new Date();
    currentDate = (date.getMonth() + 1) + "/" + date.getDate() + "/" + date.getFullYear();
    console.log("currentDate: ", currentDate)
    startTime = new Date( $(this).data("start-time") + " " + currentDate );
    endTime = new Date( $(this).data("end-time") + " " + currentDate );
    console.log("startTime: ", startTime);
    console.log("endTime: ". endTime);
    console.log("date > endTime: ", (date > endTime));
    console.log("date >= startTime: ", (date >= startTime));
    if (date > endTime) {
        $(this).addClass('pastEvent');
        $(this).find('h3').addClass('pastEvent');
        $(this).switchClass('panel-success', 'panel-default');
    }
    else if (date >= startTime) {
        $(this).switchClass('panel-success', 'panel-warning');
    }
}   

$(document).ready(function() {
    $('.radio-button').click(function() {
        $(this).closest("form").submit();
    });

    $('div.panel').each(applyPanelClass);

});
