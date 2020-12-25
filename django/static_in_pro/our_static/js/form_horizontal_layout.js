


function ajust_horizontal_form(){
	$(".field-area>div>input").addClass("form-control");
	$(".field-area textarea").addClass("form-control");
	$(".field-area select").addClass("form-control");
	//$(".field-area>label").addClass("col-sm-2 control-label"); /move col-sm-2 attr to div
	$(".field-area>div>label").addClass("control-label");
	$(".field-area>label").addClass("control-label");
	
	$(".field-area image-field a").hide()

}

$(document).ready(function(){
    ajust_horizontal_form();
});