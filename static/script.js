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
    $('div.panel').each(applyPanelClass);

    $('#sub').submit(function() {
        if (!($('#never').is(':checked') || $('#daily').is(':checked') || $('#weekly').is(':checked') || $('#eoweek').is(':checked') || $('#monthly').is(':checked'))) {
            $('#alert_1').show()
            return false;
        }
    });

    $('#sub').submit(function() {
        var t1 = $('#time').val();
        var t2 = $('#time_end').val();
        

    })

    $('.date_block').click(function(){
        var date_id = $(this).attr('id');
        var f = document.createElement("form");
        f.setAttribute('method', "get");
        f.setAttribute('action', "/date");

        var i = document.createElement("input");
        i.setAttribute('name', "date");
        i.setAttribute('value', date_id);

        f.appendChild(i);
        
        if (date_id != 0) {
            f.submit();
        }
        
    });


    $('.toggle_month').click(function(){
        var the_month = $(this).attr('id');
        var f = document.createElement("form");
        f.setAttribute('method', "get");
        f.setAttribute('action', "/calendar");
        var i = document.createElement("input");
        i.setAttribute('name', "month");
        i.setAttribute('value', the_month);
        f.appendChild(i);
        f.submit();

    });

    $('.toggle_day').click(function(){
        var the_day = $(this).attr('id');
        var f = document.createElement("form");
        f.setAttribute('method', "get");
        f.setAttribute('action', "/date");
        var i = document.createElement("input");
        i.setAttribute('name', "date");
        i.setAttribute('value', the_day)
        f.appendChild(i);
        f.submit();
    });
});
