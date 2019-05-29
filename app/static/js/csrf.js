var csrf_access_token = document.getElementById("csrf_access_token");
csrf_access_token.value = document.cookie.match(/csrf_access_token=([\w-]+)/)[1];
var csrf_refresh_token = document.getElementById("csrf_refresh_token");
csrf_refresh_token.value = document.cookie.match(/csrf_refresh_token=([\w-]+)/)[1];	