
$(document).ready(function(){

    $("#b2b_toggle_password").click(function () {
        $(this).toggleClass("fa-eye fa-eye-slash");
        var type = $(this).hasClass("fa-eye") ? "text" : "password";
        $("#password").attr("type", type);
    });
});
