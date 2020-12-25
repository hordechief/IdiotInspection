function ajust_horizontal_form(){
	//$("td.input[type='text']").addClass("form-control");
	//$(".field-area textarea").addClass("form-control");
	//$(".field-area select").addClass("form-control");
	//$(".field-area>label").addClass("col-sm-2 control-label"); /move col-sm-2 attr to div
	//$(".field-area>label").addClass("control-label");

	//$(".field-area image-field a").hide()

    $("#changelist .row2 td input").addClass('row2')
    $('#changelist .row2 td select').addClass('row2')
    $("#changelist .row1 td input").addClass('row1')
    $('#changelist .row1 td select').addClass('row1')
}

$(document).ready(function(){
    ajust_horizontal_form();
});