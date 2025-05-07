function setupPasswordToggle(toggleButtonId, passwordFieldId) {
    document.getElementById(toggleButtonId).addEventListener("click", function () {
        var passwordInput = document.getElementById(passwordFieldId);
        var icon = this.querySelector("i");

        // Toggle the password field type
        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash"); // Change icon to eye-slash
        } else {
            passwordInput.type = "password";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye"); // Change icon back to eye
        }
    });
}