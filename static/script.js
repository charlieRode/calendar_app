var displayUpdate = function() {
    var content = "Updates for version 2."
}

var updatePage = function() {
    
    $('#current_time').replaceWith('<p class="col-md-4" id="current_time">'+getCurrentTime()+'</p>');
    $('div.panel').each(applyPanelClass);
}

var getCurrentTime = function() {
    var date, hours, minutes, ampm
    date = new Date();
    hours = String(date.getHours());
    minutes = String(date.getMinutes());
    if(hours > 12){
        ampm = 'PM';
        hours -= 12;
    }
    else{
        ampm = 'AM';
    }
    if(minutes < 10){
        minutes = '0' + minutes;
    }
    if (hours == '0'){
        hours = '12';
    }
    var time = hours + ':' + minutes + ' ' + ampm;
    return time;
    
}
var applyPanelClass = function() {
    var date, currentDate, startTime, endTime;
    date = new Date();
    currentDate = (date.getMonth() + 1) + "/" + date.getDate() + "/" + date.getFullYear();
    startTime = new Date( $(this).data("start-time") + " " + currentDate );
    endTime = new Date( $(this).data("end-time") + " " + currentDate );
    if (date > endTime) {
        $(this).addClass('pastEvent');
        $(this).find('h3').addClass('pastEvent');
        $(this).switchClass('panel-success', 'panel-default');
    }
    else if (date >= startTime) {
        $(this).switchClass('panel-success', 'panel-warning');
    }
}

var invalidUsernameAlert = function() {
    var content =  '<br><div class="alert alert-warning alert-dismissible collapse" role="alert" id="alert_username"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">x</span></button><strong>Usernames may only contain alphanumeric characters and underscores.</strong></div>';
    $('#username').after(content);
    $('#alert_username').show();
}

var invalidPasswordAlert = function() {
    var content =  '<br><div class="alert alert-warning alert-dismissible collapse" role="alert" id="alert_password"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">x</span></button><strong>Passwords may only contain alphanumeric characters and underscores and must be at least 6 characters in length.</strong></div>';
    $('#password').after(content);
    $('#alert_password').show();
}

var mismatchedPassAlert = function() {
    var content =  '<br><div class="alert alert-warning alert-dismissible collapse" role="alert" id="alert_mismatch"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">x</span></button><strong>Passwords don\'t match.</strong></div>';
    $('#password_again').after(content);
    $('#alert_mismatch').show();
}


var checkForm = function() {

    var desiredUsername, password, passwordAgain, email
    desiredUsername = $('#username').val();
    password = $('#password').val();
    passwordAgain = $('#password_again').val();
    email = $('#email').val();

    var invalidChars =  '!@#$%^&*(){}[]\'"\\|:;><?/+=- ';
    var invalidUsername = false;
    for(i=0; i < invalidChars.length; i++){
        if ($.inArray(invalidChars[i], desiredUsername) != -1){
            invalidUsername = true;
        }
    }

    var invalidPassword = false;
    var mismatchedPass = false;
    if (password.length < 6){
        invalidPassword = true;
    }
    else{
        for(i=0; i < invalidChars.length; i++){
            if ($.inArray(invalidChars[i], password) != -1){
                invalidPassword = true;
            }
        }
    }

    if(password != passwordAgain){
        mismatchedPass = true;
    }

    if(invalidUsername){
        invalidUsernameAlert();
    }
    if(invalidPassword){
        invalidPasswordAlert();
    }
    if(mismatchedPass){
        mismatchedPassAlert();
    }

    if(invalidUsername || invalidPassword || mismatchedPass){
        return false;
    }
    return

}


$(document).ready(function() {
    var date, expires
    date = new Date();
    expires = new Date(2015, 6, 1);
    if (date < expires){

        if($.cookie('msg') == '1'){
            $('#notification_modal').modal('hide');
        }
        else {
            $('#notification_modal').modal('show');
            $.cookie('msg', '1', { expires: 1, path: '/' });
        }
    }

    $('#current_time').append(getCurrentTime);
    $('div.panel').each(applyPanelClass);
    var timer = setInterval(updatePage, 10000);

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
        var dateId = $(this).attr('id');
        var f = document.createElement("form");
        f.setAttribute('method', "get");
        f.setAttribute('action', "/date");

        var i = document.createElement("input");
        i.setAttribute('name', "date");
        i.setAttribute('value', dateId);

        f.appendChild(i);
        
        if (dateId != 0) {
            f.submit();
        }
        
    });


    $('.toggle_month').click(function(){
        var theMonth = $(this).attr('id');
        var f = document.createElement("form");
        f.setAttribute('method', "get");
        f.setAttribute('action', "/calendar");
        var i = document.createElement("input");
        i.setAttribute('name', "month");
        i.setAttribute('value', theMonth);
        f.appendChild(i);
        f.submit();

    });

    $('.toggle_day').click(function(){
        var theDay = $(this).attr('id');
        var f = document.createElement("form");
        f.setAttribute('method', "get");
        f.setAttribute('action', "/date");
        var i = document.createElement("input");
        i.setAttribute('name', "date");
        i.setAttribute('value', theDay)
        f.appendChild(i);
        f.submit();
    });

});
