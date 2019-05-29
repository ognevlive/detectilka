amplitude.getInstance().logEvent('get_stats');

$(document).ready(function(){
	let scroll_link = $('.scroll');
	
	scroll_link.click(function(e){
		e.preventDefault();
		let url = $('body').find($(this).attr('href')).offset().top;
		$('html, body').animate({
			scrollTop : url
		},700);
		$(this).parent().addClass('active');
		$(this).parent().siblings().removeClass('active');
		return false;	
	});
});


var topNavbar = document.getElementById("topNavbar")

var li1 = document.createElement("li");
li1.className = "nav-item"
var a1 = document.createElement("a");
a1.className = "nav-link scroll"
a1.href = "#first"
a1.innerHTML = "Popular extensions"
li1.appendChild(a1)
topNavbar.appendChild(li1)

var li2 = document.createElement("li");
li2.className = "nav-item"
var a2 = document.createElement("a");
a2.className = "nav-link scroll"
a2.href = "#second"
a2.innerHTML = "Number of malicious and safe files"
li2.appendChild(a2)
topNavbar.appendChild(li2)

var first = document.getElementById("first")
first.style.position = "relative"
first.style.height = '100vh'
first.width = '60vw'

var first = document.getElementById("second")
second.style.position = "relative"
second.style.height = '100vh'
second.width = '60vw'
