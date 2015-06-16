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
            $('#alert_1').show();
            return false;
        }
    });

    $('#sub').submit(function() {
        var t1, t2, t1_hours, t1_minutes, t1_ampm, t2_hours, t2_minutes, t2_ampm, d1, d2
        t1 = $('#time').val();
        t2 = $('#time_end').val();
        t1_hours = parseInt(t1.slice(0, 2), 10);
        t1_minutes = parseInt(t1.slice(3, 5), 10);
        t1_ampm = t1.slice(-2)
        t2_hours = parseInt(t2.slice(0, 2), 10);
        t2_minutes = parseInt(t2.slice(3, 5), 10);
        t2_ampm = t2.slice(-2);

        if ( (t1_ampm === 'PM') && (t1_hours !== 12) ) {
            t1_hours += 12;
        }

        if ( (t1_hours === 12) && (t1_ampm === 'AM') ) {
            t1_hours = 0;
        }

        if ( (t2_ampm === 'PM') && (t2_hours !== 12) ) {
            t2_hours += 12;
        }

        if ( (t2_hours === 12) && (t2_ampm === 'AM') ) {
            t2_hours = 0;
        }

        d1 = new Date(2000, 1, 1, t1_hours, t1_minutes);
        d2 = new Date(2000, 1, 1, t2_hours, t2_minutes);

        if (d2 < d1) {
            $('#alert_2').show();
            return false;
        }
    

    });

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
