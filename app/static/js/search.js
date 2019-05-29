amplitude.getInstance().logEvent('search_file_base');

$("#search_form_input").keyup(function(){
	var text = $(this).val().split(' ');
	data = {}
	for (var i = text.length - 1; i >= 0; i--) {
		if (text[i].indexOf('=') == -1) {
			key = "filename"
			value = text[i]
		}
		else {
			key = text[i].split('=')[0]
			value = text[i].split('=')[1]
		}
			data[key] = value
	}


	$.ajax({
		url: "/search_result",
		type: "get",
		data: data,

		success: function(response) {
			
			var table = $('#samplesTable').DataTable().destroy()
			$("#result").html(response);
		
			amplitude.getInstance().logEvent('search_file');
	
			var toSkip = [];
			for (var i = 1; i <= 12; i++) {
				toSkip.push(-1 * i);
			}

			$(document).ready(function () {
				var table = $('#samplesTable').DataTable({
					"pagingType": "full_numbers",
				    "bLengthChange": false,
				    "bFilter": true,
					"searching": false,
					// buttons: [ 'copy', 'excel', 'pdf', 'colvis' ],
					buttons: [ 'copy', 'excel', 'colvis' ],
					columnDefs: [
			            {
			                "targets": toSkip,
			                "visible": false
			            },
			           	{ 
			           		"max-width": "20%", 
			           		"targets": 0 
			           	},
			        ],
					"scrollX": true ,
				});

				table.buttons().container().appendTo( '#samplesTable_wrapper .col-md-6:eq(0)' );
			});
			var table =	document.getElementById('samplesTable')
			table.style.width = "100%"

		},
		error: function(xhr) {
			console.log('error')

		}
	});
});