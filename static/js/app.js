// Wait until the DOM is fully loaded before executing JavaScript
document.addEventListener("DOMContentLoaded", function () {
  /**
   * Handle the login form submission
   * This event listener captures the form data, validates it, and sends it to the backend for authentication.
   */
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault(); // Prevent default page reload behavior on form submission

      // Fetch email and password input values
      const email = document.getElementById("login-email").value;
      const password = document.getElementById("login-password").value;

      // Validate that both fields are filled
      if (!email || !password) {
        alert("Please fill in all the fields."); // Notify user if any field is empty
        return;
      }

      try {
        // Send the login credentials to the backend
        const response = await fetch("/api/login", {
          method: "POST", // Use POST to send secure data
          headers: { "Content-Type": "application/json" }, // Inform the server that the payload is JSON
          body: JSON.stringify({ email, password }), // Convert email and password into a JSON string
        });

        // Parse the server's response
        const result = await response.json();
        if (result.success) {
          // If login is successful, redirect to the home page
          window.location.href = "/home";
        } else {
          // Show an error message if login fails
          alert(result.message || "Login failed. Please try again.");
        }
      } catch (error) {
        // Handle network or other unexpected errors
        console.error("Error during login:", error); // Log the error for debugging
        alert("Login failed. Please try again."); // Notify the user of the error
      }
    });
  }

  /**
   * Handle the signup form submission
   * Captures user signup details, validates them, and sends them to the backend for user creation.
   */
  const signupForm = document.getElementById("signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault(); // Prevent page reload on form submission

      // Collect signup form data
      const form = document.getElementById("signup-form");
      const formData = {
        name: form.name.value, // User's full name
        email: form.email.value, // User's email address
        password: form.password.value, // User's password
      };

      // Ensure all required fields are filled
      if (!formData["name"] || !formData["email"] || !formData["password"]) {
        alert("Please fill in all the fields."); // Notify user if any field is missing
        return;
      }

      try {
        // Send signup data to the backend for account creation
        const response = await fetch("/api/signupform", {
          method: "POST", // Use POST for secure data submission
          headers: { "Content-Type": "application/json" }, // Indicate JSON payload
          body: JSON.stringify(formData), // Send form data as a JSON string
        });

        // Parse server's response
        const result = await response.json();
        if (response.status === 409) {
          alert("This email is already registered. Please log in.");
        } else if (result.success) {
          alert("Signup successful! Redirecting to Profile Details...");
          window.location.href = "/profile_details";
        } else {
          alert(result.message || "Signup failed. Please try again.");
        }
      } catch (error) {
        // Log and notify about any unexpected errors
        console.error("Error during signup:", error);
        alert("Signup failed. Please try again.");
      }
    });
  }

  /**
   * Handle Forgot Password Form Submission
   * Sends the email to the backend to initiate the password reset process.
   */
  const forgotPasswordForm = document.getElementById("forgot-password-form");
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async (event) => {
      event.preventDefault(); // Prevent form reload behavior

      const email = document.getElementById("reset-email").value; // Fetch the email input value

      // Ensure the email field is filled
      if (!email) {
        alert("Please enter your email."); // Notify user to fill in the email
        return;
      }

      try {
        // Send the email to the backend for password reset
        const response = await fetch("/forgot-password", {
          method: "POST", // Use POST for secure submission
          headers: { "Content-Type": "application/json" }, // Specify JSON payload
          body: JSON.stringify({ email }), // Send email as JSON string
        });

        // Notify user of the result
        const result = await response.json();
        alert(result.message || "Password reset link sent successfully.");
      } catch (error) {
        console.error("Error during password reset:", error); // Log error for debugging
        alert("Failed to send reset link. Please try again."); // Notify user
      }
    });
  }
});

/**
 * Toggles the visibility of the profile dropdown menu
 */
function toggleDropdown() {
  const dropdownMenu = document.getElementById("dropdown-menu");
  dropdownMenu.classList.toggle("show"); // Add/remove 'show' class to toggle visibility
}

/**
 * Redirects the user to the login page for logout
 */
function logout() {
  window.location.href = '{{ url_for("login") }}'; // Redirect to login page
}
