document.addEventListener('DOMContentLoaded', function () {
	document.getElementById('btn4').addEventListener('submit', function doThings() { 
		amplitude.getInstance().logEvent('upload_file');
		var csrf_access_token = document.getElementById('csrf2')
		csrf_access_token.value = document.cookie.match(/csrf_access_token=([\w\d-]+)/)[1];

		var csrf_refresh_token = document.getElementById('csrf3')
		csrf_refresh_token.value = document.cookie.match(/csrf_refresh_token=([\w\d-]+)/)[1];
	});		
});


$(".custom-file-input").on("change", function() {
  var fileName = $(this).val().split("\\").pop();
  $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});

var checkDiv = setInterval(function(){
	var buttons = document.getElementsByClassName("dt-buttons btn-group")
	if (buttons[0] != undefined) {
		var pdf   = buttons[0].children[2]
		var excel = buttons[0].children[1]

		pdf.onclick = function () {
			amplitude.getInstance().logEvent('download_pdf');
		}

		excel.onclick = function () {
			amplitude.getInstance().logEvent('download_excel');
		}
       	clearInterval(checkDiv);
	} 
}, 100); 
