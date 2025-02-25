let currentQuestionIndex = 0;
let timerInterval;
let timeLeft = 20;
let score = 0;

function startQuiz() {
  console.log("Starting Quiz...");
  loadQuestion();
  startTimer();
}

function loadQuestion() {
  try {
    const questionBlock = document.getElementById("question-block");
    const nextButton = document.getElementById("next-question");

    questionBlock.innerHTML = "";
    console.log("reached for acccesing questions at ", new Date());
    console.log("Type of quizQuestions", typeof quizQuestions);
    console.log("quizQuestions", quizQuestions);
    const question = quizQuestions[currentQuestionIndex];
    console.log("Current Question:", question);

    const questionHTML = `
        <p>${currentQuestionIndex + 1}. ${escapeHTML(question.question)}</p>
        ${question.options
          .map(
            (option) => `
                <label>
                    <input type="radio" name="option" value="${escapeHTML(
                      option
                    )}" onclick="enableNextButton()">
                    ${escapeHTML(option)}
                </label>
            `
          )
          .join("<br>")}
    `;
    questionBlock.innerHTML = questionHTML;

    nextButton.disabled = true;
  } catch (error) {
    console.log("Getting Error in loadQuestion", error);
  }
}

function startTimer() {
  timeLeft = 20;
  const timerDisplay = document.getElementById("time-remaining");

  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    timeLeft--;
    timerDisplay.textContent = `${timeLeft}`;

    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      handleTimeOut();
    }
  }, 1000);
}

function enableNextButton() {
  document.getElementById("next-question").disabled = false;
}

function handleTimeOut() {
  alert("Time's up!");
  loadNextQuestion();
}

function loadNextQuestion() {
  const selectedOption = document.querySelector('input[name="option"]:checked');
  const nextButton = document.getElementById("next-question");

  if (selectedOption) {
    const answer = selectedOption.value;
    quizQuestions[currentQuestionIndex]["user_answer"] = answer;
    if (answer === quizQuestions[currentQuestionIndex].correct_answer) {
      quizQuestions[currentQuestionIndex]["is_correct"] = true;
      score++;
      // Show correct animation
      showAnimation("correct");
      selectedOption.parentElement.style.color = "green"; // Highlight correct answer
    } else {
      quizQuestions[currentQuestionIndex]["is_correct"] = false;
      showAnimation("incorrect");
      selectedOption.parentElement.style.color = "red"; // Highlight wrong answer

      // Highlight the correct answer
      const correctOption = Array.from(
        document.querySelectorAll('input[name="option"]')
      ).find(
        (input) =>
          input.value === quizQuestions[currentQuestionIndex].correct_answer
      );
      if (correctOption) {
        correctOption.parentElement.style.color = "green";
      }
    }

    // Disable all options to prevent further clicks
    document
      .querySelectorAll('input[name="option"]')
      .forEach((input) => (input.disabled = true));
  }

  // Wait for 2 seconds before loading the next question
  setTimeout(() => {
    currentQuestionIndex++;
    if (currentQuestionIndex < quizQuestions.length) {
      loadQuestion();
      startTimer();
    } else {
      endQuiz();
    }
  }, 2000);

  nextButton.disabled = true; // Disable "Next" button
}

function endQuiz() {
  clearInterval(timerInterval);
  const questionBlock = document.getElementById("question-block");
  const timer = document.getElementById("timer");
  const nextButton = document.getElementById("next-question");
  const current_quiz_topic = topic;
  const current_quiz_difficulty = difficulty;
  // Hide timer and next button
  timer.style.display = "none";
  nextButton.style.display = "none";
  console.log("quizQuestionsquizQuestions", quizQuestions);
  // Prepare quiz results for submission
  const quizResults = quizQuestions.map((question, index) => ({
    question: question.question,
    correct_answer: question.correct_answer,
    user_answer: question.user_answer,
    explanation: question.explanation,
    is_correct:
      document.querySelector(`input[name="option"]:checked`)?.value ===
      question.correct_answer,
  }));

  // Display final score and home button
  questionBlock.innerHTML = `
          <h2>Quiz Completed!</h2>
          <p>Your Score: ${score} / ${quizQuestions.length}</p>
          <button id="home-button" class="home-btn" onclick="redirectToHome()">Go to Home</button>
      `;

  // Send data to backend
  sendQuizResults(
    quizResults,
    score,
    current_quiz_topic,
    current_quiz_difficulty
  );
}

// Function to send quiz results to backend
async function sendQuizResults(quizResults, score, topic, difficulty) {
  try {
    const response = await fetch("/submit_quiz_results", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        quiz_id: crypto.randomUUID(), // Generate unique quiz ID
        topic: topic, // Replace with dynamic topic
        difficulty: difficulty, // Replace with dynamic difficulty
        total_score: score,
        quiz_date: new Date().toISOString(),
        quiz_details: quizResults, // Send the entire quiz as JSON
      }),
    });

    if (response.ok) {
      console.log("Quiz results submitted successfully");
    } else {
      console.error("Failed to submit quiz results");
    }
  } catch (error) {
    console.error("Error submitting quiz results:", error);
  }
}

// Redirect to home page
function redirectToHome() {
  window.location.href = "/home"; // Adjust the path based on your application's home page URL
}

// Function to escape HTML special characters
function escapeHTML(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

document
  .getElementById("next-question")
  .addEventListener("click", loadNextQuestion);

// Function to show animations
function showAnimation(type) {
  console.log("type", type);
  const animationContainer = document.getElementById("quiz-animation");
  animationContainer.innerHTML = ""; // Clear previous animation

  if (type == "correct") {
    const tenorEmbed = document.createElement("div");
    tenorEmbed.classList.add("tenor-gif-embed");
    tenorEmbed.setAttribute("data-postid", "2118779316988239840"); // Post ID for incorrect animation
    tenorEmbed.setAttribute("data-share-method", "host");
    tenorEmbed.setAttribute("data-aspect-ratio", "0.566265");
    tenorEmbed.setAttribute("data-width", "100%");
    tenorEmbed.innerHTML = `<a href="https://tenor.com/view/cool-fun-white-cat-dance-cool-and-fun-times-gif-2118779316988239840">Cool Fun GIF</a>from <a href="https://tenor.com/search/cool-gifs">Cat GIFs</a>`;
    animationContainer.appendChild(tenorEmbed);
    // Add Tenor GIF for correct answer
  } else if (type === "incorrect") {
    // Add a different Tenor GIF for incorrect answer
    const tenorEmbed = document.createElement("div");
    tenorEmbed.classList.add("tenor-gif-embed");
    tenorEmbed.setAttribute("data-postid", "23690916"); // Post ID for correct animation
    tenorEmbed.setAttribute("data-share-method", "host");
    tenorEmbed.setAttribute("data-aspect-ratio", "0.553125");
    tenorEmbed.setAttribute("data-width", "100%");
    tenorEmbed.innerHTML = `<a href="https://tenor.com/view/the-cat-is-kicking-the-other-cat-gif-23690916">The Cat Is Kicking The Other Cat GIF</a>from <a href="https://tenor.com/search/the+cat+is+kicking+the+other+cat-gifs">The Cat Is Kicking The Other Cat GIFs</a>`;
    animationContainer.appendChild(tenorEmbed);
  }

  // Dynamically load the Tenor embed script
  const tenorScript = document.createElement("script");
  tenorScript.src = "https://tenor.com/embed.js";
  tenorScript.async = true;
  animationContainer.appendChild(tenorScript);

  // Remove the animation after 2 seconds
  setTimeout(() => {
    animationContainer.innerHTML = "";
  }, 4000);
}

startQuiz();
