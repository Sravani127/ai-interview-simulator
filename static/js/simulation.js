let currentQuestionIndex = 0; // Tracks the current question index
const totalQuestions = 5; // Total number of questions in the simulation
const questionDuration = 30; // Time allocated for each question in seconds
let timerInterval; // To store the interval ID for the timer
let remainingTime = questionDuration; // Initialize remaining time

// Example questions (replace with API calls or dynamic data)
const questions = [
  "What is the time complexity of binary search?",
  "Explain the concept of polymorphism in OOP.",
  "What is the difference between REST and GraphQL?",
  "Describe the CAP theorem in distributed systems.",
  "What are the advantages of using microservices architecture?",
];

// User answers storage
const userAnswers = [];

// Load the first question on page load
document.addEventListener("DOMContentLoaded", () => {
  loadQuestion();
  startTimer();
});

/**
 * Load the current question into the UI
 */
function loadQuestion() {
  // Update question number
  const questionNumberElement = document.getElementById("question-number");
  questionNumberElement.textContent = `Question ${
    currentQuestionIndex + 1
  } of ${totalQuestions}`;

  // Update question text
  const questionTextElement = document.getElementById("question-text");
  questionTextElement.textContent = questions[currentQuestionIndex];

  // Reset user answer text area
  const userAnswerElement = document.getElementById("user-answer");
  userAnswerElement.value = ""; // Clear the previous answer
}

/**
 * Start the timer for the current question
 */
function startTimer() {
  // Clear any existing timer
  clearInterval(timerInterval);

  remainingTime = questionDuration; // Reset remaining time
  const timerElement = document.getElementById("timer");

  // Update the timer display every second
  timerInterval = setInterval(() => {
    if (remainingTime > 0) {
      remainingTime -= 1; // Decrement time
      timerElement.textContent = `Time left: ${remainingTime}s`; // Update timer text
    } else {
      // Time's up for the current question
      clearInterval(timerInterval);
      alert("Time's up! Moving to the next question."); // Notify the user
      nextQuestion(); // Automatically move to the next question
    }
  }, 1000);
}

/**
 * Handle moving to the next question
 */
function nextQuestion() {
  // Save the user's current answer
  const userAnswerElement = document.getElementById("user-answer");
  userAnswers[currentQuestionIndex] = userAnswerElement.value.trim();

  // Check if there are more questions
  if (currentQuestionIndex < totalQuestions - 1) {
    currentQuestionIndex += 1; // Move to the next question
    loadQuestion(); // Load the next question
    startTimer(); // Restart the timer
  } else {
    // No more questions; alert the user
    alert("You have completed all questions. Please submit your simulation.");
  }

  // Update progress bar
  updateProgressBar();
}

/**
 * Update the progress bar based on the current question
 */
function updateProgressBar() {
  const progressBar = document.getElementById("progress-bar");
  const progressPercentage =
    ((currentQuestionIndex + 1) / totalQuestions) * 100;
  progressBar.style.width = `${progressPercentage}%`; // Update progress bar width
}

/**
 * Submit the simulation and send answers to the server
 */
function submitSimulation() {
  // Save the user's current answer (if any)
  const userAnswerElement = document.getElementById("user-answer");
  userAnswers[currentQuestionIndex] = userAnswerElement.value.trim();

  // Stop the timer
  clearInterval(timerInterval);

  // Prepare the data payload
  const payload = {
    answers: userAnswers,
    timestamp: new Date().toISOString(),
  };

  // Send the data to the server
  fetch("/api/submit_simulation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload), // Convert the answers to JSON format
  })
    .then((response) => response.json())
    .then((result) => {
      if (result.success) {
        alert("Simulation submitted successfully!"); // Notify success
        window.location.href = "/home"; // Redirect to home page or results page
      } else {
        alert(
          result.message || "Failed to submit the simulation. Please try again."
        );
      }
    })
    .catch((error) => {
      console.error("Error submitting simulation:", error);
      alert("An error occurred while submitting your simulation.");
    });
}
