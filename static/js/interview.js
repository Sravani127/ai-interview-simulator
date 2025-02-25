const socket = io(); // Connect to WebSocket
const chatArea = document.getElementById("chat-area");
const aiQuestion = document.getElementById("ai-question");
const startButton = document.getElementById("start-btn");
let interviewActive = false;
// Start the interview
document.getElementById("start-btn").addEventListener("click", () => {
  if (!interviewActive) {
    // Start the interview
    socket.emit("start_interview");
    startButton.textContent = "End Interview";
    interviewActive = true;
  } else {
    // End the interview
    stopAudio();
    socket.emit("end_interview");
    // Show loading modal
    showLoadingModal();
    startButton.textContent = "End Interview";
    startButton.disabled = true;
    aiQuestion.textContent = "User has ended the Interview.";
    interviewActive = false;
  }
});

// Show a loading modal when ending the interview
function showLoadingModal() {
  const loadingModal = document.createElement("div");
  loadingModal.classList.add("loading-modal");
  loadingModal.innerHTML = `
    <div class="loading-modal-content">
      <p>Processing your interview, please wait...</p>
      <div class="spinner"></div>
    </div>
  `;
  document.body.appendChild(loadingModal);
}

// Hide the loading modal
function hideLoadingModal() {
  const loadingModal = document.querySelector(".loading-modal");
  if (loadingModal) {
    loadingModal.remove();
  }
}

function stopAudio() {
  if (window.currentAudio) {
    window.currentAudio.pause();
    window.currentAudio.currentTime = 0;
    console.log("Ongoing audio playback stopped on the client.");
  }
}

// Listen for real-time chat updates
socket.on("update_chat", (data) => {
  updateChat(data.sender, data.message);
});

// Listen for live transcription updates
socket.on("update_typing", (data) => {
  document.getElementById("ai-question").textContent = `User: ${data.message}`;
});

// Update chat area dynamically
function updateChat(sender, message) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add(sender === "AI" ? "ai-message" : "user-message");
  messageDiv.textContent = `${sender}: ${message}`;
  chatArea.appendChild(messageDiv);
  chatArea.scrollTop = chatArea.scrollHeight;

  // Update visible question for AI
  if (sender === "AI") {
    aiQuestion.textContent = message;
  }
}

/**
 * Send the user's response to the server and handle the next steps in the interview.
 */
function sendResponse() {
  // Get the user's response from the input field
  const userInput = document.getElementById("user-input").value.trim();

  // Validate that the input is not empty
  if (!userInput) {
    alert("Please type a response before sending.");
    return;
  }

  // Append the user's response to the chat area
  appendMessage("You", userInput);

  // Clear the input field
  document.getElementById("user-input").value = "";

  // Send the user's response to the server via Socket.IO
  socket.emit("user_response", {
    question: currentQuestion, // Send the current question for context
    response: userInput, // Send the user's response
  });

  // Listen for the next question from the server
  socket.on("ai_question", (data) => {
    currentQuestion = data.question; // Update the current question
    appendMessage("AI", currentQuestion); // Display the next question in the chat
    document.getElementById("ai-question").textContent = currentQuestion; // Update the main question display
  });
}

/**
 * Append a message to the chat area.
 * @param {string} sender - The sender of the message ("You" or "AI").
 * @param {string} message - The message content.
 */
function appendMessage(sender, message) {
  const chatArea = document.getElementById("chat-area");

  // Create a new message div
  const messageDiv = document.createElement("div");
  messageDiv.classList.add(
    "message",
    sender === "You" ? "user-message" : "ai-message"
  );

  // Set the message content
  messageDiv.textContent = `${sender}: ${message}`;

  // Append the message to the chat area
  chatArea.appendChild(messageDiv);

  // Automatically scroll to the bottom of the chat area
  chatArea.scrollTop = chatArea.scrollHeight;
}

socket.on("interview_summary", (data) => {
  hideLoadingModal(); // Hide the loading modal
  displayFeedback(data.score, data.feedback);
});

function displayFeedback(score, feedback) {
  // Create a modal container
  const modal = document.createElement("div");
  modal.classList.add("feedback-modal");

  // Modal content
  modal.innerHTML = `
      <div class="feedback-modal-content">
          <h2>Interview Summary</h2>
          <div class="feedback-score">
              <p><strong>Score:</strong> ${score}</p>
          </div>
          <div class="feedback-text">
              <p><strong>Feedback:</strong> ${feedback}</p>
          </div>
          <button class="close-btn" onclick="closeFeedbackModal()">Close</button>
      </div>
  `;

  // Append the modal to the body
  document.body.appendChild(modal);
}

function closeFeedbackModal() {
  const modal = document.querySelector(".feedback-modal");
  if (modal) {
    modal.remove();
  }
  window.location.href = "/home";
}
