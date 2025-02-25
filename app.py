from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_socketio import SocketIO
import pyttsx3
import speech_recognition as sr
import threading
import os
import json
from elevenlabs.client import ElevenLabs  # For text-to-speech (TTS) functionality using ElevenLabs
from elevenlabs import stream
from openai import OpenAI
import boto3  # AWS SDK for Python to interact with AWS services like S3, Cognito, etc.
import assemblyai as aai  # For speech-to-text processing using AssemblyAI
import psycopg2
from werkzeug.utils import secure_filename
import hmac
from dotenv import load_dotenv
import hashlib
import base64
import re
import uuid
from datetime import datetime
import time
# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your_unique_secret_key'
socketio = SocketIO(app)
load_dotenv()
# Initialize Text-to-Speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # Adjust speaking rate
engine.setProperty("volume", 1.0)  # Set volume level

# AWS Cognito Configuration
USER_POOL_ID = os.getenv("USER_POOL_ID")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
APP_CLIENT_SECRET = os.getenv("APP_CLIENT_SECRET")

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION")


# Redshift Configuration
REDSHIFT_HOST = os.getenv("REDSHIFT_HOST")
REDSHIFT_PORT = os.getenv("REDSHIFT_PORT")
REDSHIFT_USER = os.getenv("REDSHIFT_USER")
REDSHIFT_PASSWORD = os.getenv("REDSHIFT_PASSWORD")
REDSHIFT_DB = os.getenv("REDSHIFT_DB")

# S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)

# Cognito client
# AWS Cognito client initialization
# Used for user authentication, sign-up, and sign-in operations
# AWS S3 client initialization
# Used for file uploads (e.g., storing resumes or user assets) and retrieval
client = boto3.client("cognito-idp", 
                      region_name=S3_REGION,
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY)
interviewEnded = False

class AI_Assistant:
    """
    AI_Assistant Class
    ------------------
    This class encapsulates the functionality of the AI assistant used in the platform.
    
    **Purpose**:
    1. Handle text-to-speech (TTS) functionality using ElevenLabs.
    2. Convert speech (audio) to text using AssemblyAI.
    3. Synchronize TTS and STT for creating lifelike interview simulations.

    **Methods**:
    - `generate_audio_response(text)`: Converts text input into lifelike audio output using ElevenLabs.
    - `transcribe_audio(audio_file_path)`: Transcribes speech from an audio file into text using AssemblyAI.
    - `synchronize_audio_video(text, avatar_video)`: (Planned) Synchronizes generated audio with a video avatar.
    """
     

    def __init__(self, difficulty=None, topic=None, focus=None):
        """
        Initializes the AI Assistant with required API keys and configurations
        for ElevenLabs and AssemblyAI services.
        """
        # Initialize ElevenLabs API configuration
        # ElevenLabs is used for generating natural-sounding text-to-speech (TTS)
        # Initialize AssemblyAI client with the provided API key
        aai.settings.api_key = os.getenv("ASSEMBLY_AI_API_KEY") # AssemblyAI API Key Used for speech-to-text processing in AI-driven interview simulations

        self.openai_client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
        self.elevenlabs_api_key = os.getenv("ELVEN_LABS_API_KEY")
        self.client = ElevenLabs(
        api_key=os.getenv("ELVEN_LABS_API_KEY"), # ElevenLabs API Key Used for generating lifelike audio from text in interview simulations
        )
        self.audio_stream = None
        self.transcriber = None
        self.interviewEnded = interviewEnded



    def initialize_interview(self, difficulty, topic, focus):
                # Prompt
        self.full_transcript = [
            {"role":"system", 
             "content":f"You are an AI Interviewer and you have to mock interview a candidate so be professional and strict on the candidate, The person you are interviewing is here to interview for the topic {topic} and mostly focus on the  {focus} interview type. So ask the user some {difficulty} questions. Ask only one question at a time. Consider the User response before asking the next question."
            },
        ]
        self.interview_difficulty = difficulty
        self.interview_topic = topic
        self.interview_focus = focus

    def get_interview_details(self):
        return json.dumps({"difficulty": self.interview_difficulty, "topic": self.interview_topic, "focus": self.interview_focus})


###### Step 2: Real-Time Transcription with AssemblyAI ######
        
    def start_transcription(self):
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate = 16000,
            on_data = self.on_data,
            on_error = self.on_error,
            on_open = self.on_open,
            on_close = self.on_close,
            end_utterance_silence_threshold = 1000
        )

        self.transcriber.connect()
        microphone_stream = aai.extras.MicrophoneStream(sample_rate =16000)
        self.transcriber.stream(microphone_stream)
    
    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        # print("Session ID:", session_opened.session_id)
        return


    def on_data(self, transcript: aai.RealtimeTranscript):
        if not transcript.text or self.interviewEnded:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.generate_ai_response(transcript)
        else:
            socketio.emit('update_typing', {'message': transcript.text})
            # print(transcript.text, end="\r")


    def on_error(self, error: aai.RealtimeError):
        print("An error occured:", error)
        return


    def on_close(self):
        print("Closing Session")
        return

###### Step 3: Pass real-time transcript to OpenAI ######
    
    def generate_ai_response(self, transcript):
        if not self.interviewEnded:

            self.stop_transcription()

            self.full_transcript.append({"role":"user", "content": transcript.text})
            # print(r"\User: {transcript.text}", end="\r\n")
            socketio.emit('update_chat', {'sender': 'User', 'message': transcript.text})

            response = self.openai_client.chat.completions.create(
                model = "gpt-3.5-turbo",
                messages = self.full_transcript
            )
            ai_response = response.choices[0].message.content
            self.generate_audio(ai_response)
            self.start_transcription()


    def evaluate_response(self,responses_history):
        responses_history.pop(0)
        responses_history.insert(0,{'role':'system', 'content': 'You need to evaluate and provide score for a discussion happened between a user and assistant.\n Based on the below conversation between assistant and user , Evaluate the User responses for the questions asked by the assistant based on clarity, relevance, and conciseness .\n If you are not able to find any meaningful conversation then provide the Score as 0 and feedback as the No valid conversation to give feedback. \n Provide a score out of 100 and give specific feedback for each of user statement based on the questions asked by the assistant. \n Give the final response as Object with overall_score which is a integer and feedback which is a string , dont add anything else apart from overall_score,feedback in the response'})
        try:
            result = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages= responses_history
            )
            response = result.choices[0].message.content
            print("response",type(response))
            print("response",response)
            print("responses_history",responses_history)
            result_json_object = json.loads(response)
            score = result_json_object["overall_score"]  # Extract score
            feedback = result_json_object["feedback"]  # Extract feedback
            return score, feedback
        except Exception as e:
            score = 0
            feedback = "Not Able to provide any feedback based on the conversation between the User & AI Interviewer."
            return score, feedback
###### Step 4: Generate audio with ElevenLabs ######
 
    def generate_audio(self, text):
        """
            Generate lifelike audio from text using ElevenLabs API.

            Args:
                text (str): The text to convert into speech.

            Returns:
                str: Path to the generated audio file.
        """
        try:
            self.full_transcript.append({"role":"assistant", "content": text})
            socketio.emit('update_chat', {'sender': 'AI', 'message': text})
            # print(f"\nAI Receptionist: {text}")
            self.audio_streaming = True
            self.audio_stream = self.client.generate(
                text = text,
                stream = True
            )

            stream(self.audio_stream)
        except Exception as e:
            print(f"Error during audio generation: {e}")

    def stop_audio(self):
        """
        Stop any ongoing audio playback.
        """
        if self.audio_stream:
            try:
                print("Stopping audio stream...")
                self.audio_stream.close()  # Close the stream if supported
                self.audio_stream = None
            except Exception as e:
                print(f"Error stopping audio stream: {e}")

ai_assistant = AI_Assistant()
# Current question index
current_index = 0

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login')
def loginPage():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/profile_details', methods=['GET', 'POST'])
def profile_details():
    name = session.get('name', '')
    email = session.get('email', '')
    unique_Id_for_user = getUniqueIdForUser(email)
    if request.method == 'POST':
        try:
            # Extract form data
            phone = request.form.get('phone')
            job_title = request.form.get('job_title')
            experience = request.form.get('experience')
            industry = request.form.get('industry')
            job_role = request.form.get('job_role')
            skills = request.form.get('skills')
            interests = request.form.get('interests')
            focus = request.form.get('focus')
            qualification = request.form.get('qualification')
            field_of_study = request.form.get('field_of_study')
            university = request.form.get('university')
            certifications = request.form.get('certifications')
            resume = request.files.get('resume')
            # Upload resume to S3
            if resume:
                filename = secure_filename(resume.filename)
                s3_key = f"resumes/{unique_Id_for_user}/{filename}"
                s3_client.upload_fileobj(
                    resume,
                    S3_BUCKET_NAME,
                    s3_key
                )
                resume_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
            else:
                resume_url = None
            # Insert data into Redshift
            conn = psycopg2.connect(
                host=REDSHIFT_HOST,
                port=REDSHIFT_PORT,
                dbname=REDSHIFT_DB,
                user=REDSHIFT_USER,
                password=REDSHIFT_PASSWORD
            )
            cursor = conn.cursor()
            unique_Id_for_user = getUniqueIdForUser(email)
            insert_query = """
                INSERT INTO user_profile_data (
                    unique_id, name, email, phone, job_title, experience, industry, role,
                    skills, interests, focus, qualification, field_of_study, university,
                    certifications, resume_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                unique_Id_for_user, name, email, phone, job_title, experience, industry, job_role,
                skills, interests, focus, qualification, field_of_study, university,
                certifications, resume_url
            ))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('home'))
        except Exception as e:
            return f"Error: {str(e)}", 500
    return render_template('profile_details.html', name=name, email=email)

def getUniqueIdForUser(email):
    local_part = email.split("@")[0]
    unique_identifier = re.sub(r'[^a-zA-Z0-9]', '', local_part)
    unique_identifier = unique_identifier.lower()
    session['unique_id'] = unique_identifier
    return unique_identifier


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    email = session.get('email')  # Assuming the user's email is stored in session
    uniqueId_for_user = getUniqueIdForUser(email)
    if not email:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    try:
        # Connect to Redshift
        conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
        cursor = conn.cursor()

        if request.method == 'POST':
            # Update the profile details
            job_title = request.form.get('job_title')
            experience = request.form.get('experience')
            new_resume = request.files.get('resume')

            # Fetch current resume URL for the user
            cursor.execute("SELECT resume_url FROM user_profile_data WHERE email = %s", (email,))
            current_resume_url = cursor.fetchone()[0]

            # Upload new resume to S3 if provided
            if new_resume:
                # Extract file name and upload to S3
                filename = secure_filename(new_resume.filename)
                s3_key = f"resumes/{uniqueId_for_user}/{filename}"
                s3_client.upload_fileobj(
                    new_resume,
                    S3_BUCKET_NAME,
                    s3_key
                )
                resume_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
            else:
                resume_url = current_resume_url  # Keep the existing resume URL if no new file is uploaded

            # Update the database with new details
            update_query = """
                UPDATE user_profile_data
                SET job_title = %s, experience = %s, resume_url = %s
                WHERE email = %s and unique_id = %s
            """
            cursor.execute(update_query, (job_title, experience, resume_url, email, uniqueId_for_user))
            conn.commit()

            return redirect(url_for('home'))  # Redirect to home or success page

        else:
            # Fetch user details for GET request
            cursor.execute("SELECT name, email, phone, job_title, experience, industry, role, skills, interests, focus, qualification, field_of_study, university, certifications, resume_url FROM user_profile_data WHERE email = %s", (email,))
            user_data = cursor.fetchone()

            # Render the Edit Profile page with pre-filled data
            return render_template('edit_profile.html', user_data=user_data)

    except Exception as e:
        return f"Error: {str(e)}", 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def calculate_secret_hash(client_id, client_secret, username):
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/home')
def home():
    try:
        return render_template('home.html',name=session.get('name', 'User'))
    except Exception as e:
        return f"Error: {e}", 500

def check_user_exists(email):
    try:
        response = client.list_users(
            UserPoolId=USER_POOL_ID,
            Filter=f'email = "{email}"',
        )
        if response["Users"]:
            return True  # User exists
        else:
            return False  # User does not exist
    except Exception as e:
        print("Error during user check:", str(e))
        return False

# Login route
@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400
    
    secret_hash = calculate_secret_hash(APP_CLIENT_ID, APP_CLIENT_SECRET, email)
    try:
        # Authenticate user
        response = client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
                "SECRET_HASH": secret_hash,  # Include the secret hash
            },
            ClientId=APP_CLIENT_ID,
        )
        session["email"] = email
        session["unique_id"] = email.split("@")[0]
        return jsonify({
                "success": True,
                "message": "Login successful.",
                "id_token": response["AuthenticationResult"]["IdToken"],
                "access_token": response["AuthenticationResult"]["AccessToken"],
            }), 200
    except client.exceptions.NotAuthorizedException as e:
        return jsonify({"success": False, "message": "Invalid credentials."}), 401
    except client.exceptions.UserNotFoundException:
        return jsonify({"success": False, "message": "User not found."}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/signupform", methods=["POST"])
def signupForm():
    """
    API Endpoint: Signup Form
    -------------------------
    This endpoint handles user signup by validating the provided details
    (name, email, and password) and creating the user in AWS Cognito.

    Workflow:
    1. Validate input data.
    2. Check if the user already exists in Cognito.
    3. If the user does not exist, create a new user in Cognito.
    4. Set a permanent password for the user.
    5. Return appropriate success or error responses.

    Returns:
        JSON response with success or failure messages.
    """
    data = request.get_json()
    # Extract fields from the request payload
    email = data.get("email")  # User's email address
    password = data.get("password")  # User's desired password
    name = data.get("name")  # User's name (optional but assumed in this example)
    if not email or not password or not name:
        return jsonify({"success": False, "message": "All fields are required."}), 400
    try:
        if check_user_exists(email):
            return jsonify({"success": False, "message": "User Already Exists."})
        else:
            response = client.admin_create_user(
                UserPoolId=USER_POOL_ID,
                Username=email,  # Use email as the username
                TemporaryPassword=password,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "True"}
                ],
            )
            client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=email,
                Password=password,
                Permanent=True
            )

            session["email"] = email
            session["name"] = name
            return jsonify({"success": True, "message": "User signed up successfully."})

    except Exception as e:
        print("Error during user creation:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    try:
        # Get the selected values from the form
        difficulty = request.form.get('difficulty')
        topic = request.form.get('topic')
        focus = request.form.get('focus')
        interview_type = request.form.get('interview_type')
        print(f"Difficulty: {difficulty}, Topic: {topic}, Focus: {focus}, Interview Type: {interview_type}")

        if interview_type.lower() == "quiz":
            questionsObject = generate_questions_for_quiz(difficulty, topic, focus, ai_assistant)
            print("questionsObject at 537",questionsObject)
            time.sleep(4)
            return render_template("quiz_simulation.html", questions=questionsObject, difficulty=difficulty,topic=topic)
        
        if interview_type.lower() == "mock_interview":
            ai_assistant.initialize_interview(difficulty, topic, focus)
            return render_template("interview_simulation.html", name=session.get('name', 'User'))
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/prepare_for_quiz')
def prepare_for_quiz():
    return render_template('prepare_for_quiz.html', interview_type='quiz',name=session.get('name', 'User'))

@app.route('/prepare_for_interview')
def prepare_for_interview():
    return render_template('prepare_for_interview.html', interview_type='mock_interview',name=session.get('name', 'User'))

#generate questions for quiz type preparation
def generate_questions_for_quiz(difficulty, topic, focus, ai_assistant):
        try:
            prompt = (
                f"Generate 10 {difficulty} level question on {topic}. Don't repeat same questions "
                f"Provide 4 multiple-choice options and indicate the correct answer and a small explanation regarding the correct answer. Give the response as a Array of Objects string not with backticks. Each Object with question , options, correct_answer, explanation .Don't add anything else in the response, just the question , options, correct_answer, explantion only"
            )
            print(f"promptpromptprompt",prompt)
            result = ai_assistant.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "developer", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            response = result.choices[0].message.content
            print(f"responseresponseresponse",result)
            questions_json_object = json.loads(response)
            return questions_json_object
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500


def escape_strings(data):
    if isinstance(data, dict):
        return {k: escape_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [escape_strings(i) for i in data]
    elif isinstance(data, str):
        return data.replace('"', '\\"').replace("'", "\\'")
    return data

# Forgot Password route
@app.route('/forgot-password', methods=['POST'])
def handle_forgot_password():
    data = request.get_json()
    email = data.get('email')

    if email in USER_DB:
        return jsonify({"success": True, "message": f"Password reset link sent to {email}"}), 200
    return jsonify({"success": False, "message": "Email not found"}), 404

@app.route('/prepare')
def prepare():
    return render_template('prepare.html',name=session.get('name', 'User'))

@app.route('/quiz-simulation')
def quiz_simulation():
    return render_template('quiz_simulation.html')

@app.route('/interview-simulation')
def interview_simulation():
    return render_template('interview_simulation.html',name=session.get('name', 'User'))


@socketio.on('start_interview')
def start_interview():
    ai_assistant.interviewEnded = False
    greeting = "Thank you for joining the call. My name is Sandy, shall we start with the interview?"
    ai_assistant.generate_audio(greeting)
    ai_assistant.start_transcription()

@socketio.on("end_interview")
def end_interview():
    """
    Event Listener: end_interview
    -----------------------------
    This function handles the "end_interview" Socket.IO event triggered from the client-side
    when the interview session is terminated. It performs the following actions:

    1. Marks the interview as ended.
    2. Generates a closing statement audio using the AI Assistant.
    3. Stops any ongoing transcription processes.
    4. Evaluates the user's responses, computes the total score, and generates feedback.
    5. Emits the interview summary (score and feedback) back to the client.
    6. Notifies the client chat that the interview has ended.

    Emits:
        - "interview_summary": Sends the final score and feedback.
        - "update_chat": Notifies the chat about the interview conclusion.
    """
    if ai_assistant:
        if hasattr(ai_assistant, "stop_audio"):
            ai_assistant.stop_audio()
        ai_assistant.interviewEnded = True
        closing_statement = "Thank you for joining the call. We have recorded all your responses and will come back to you with our response."
        ai_assistant.generate_audio(closing_statement)
        ai_assistant.stop_transcription()
        ai_assistant.on_close()
    # Analyze each user response and compute the total score
    responses_history = ai_assistant.full_transcript
    score, feedback = ai_assistant.evaluate_response(responses_history)
    print(f"responses_history",responses_history)
    interview_details_data = ai_assistant.get_interview_details()
    save_transcript_to_s3(responses_history, score, feedback, interview_details_data)


    # Emit the final score and feedback
    socketio.emit("interview_summary", {"score": score, "feedback": feedback})
    socketio.emit("update_chat", {"sender": "system", "message": "The interview has been ended."})



def insert_into_redshift(interview_id, user_id, interview_date, s3_url, total_score, feedback, topic, difficulty, focus):
    # Redshift connection
    conn = psycopg2.connect(
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD,
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT
        )
    cursor = conn.cursor()
    cursor_for_goal_table = conn.cursor()
    cursor.execute(
            """
            INSERT INTO interview_history (
                user_id, 
                interview_id,
                interview_date, 
                s3_url,
                score,
                feedback,
                topic,
                difficulty,
                focus
            ) 
            VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s)
            """,
            (
                user_id,  # Assuming user_id is stored in session
                interview_id,
                interview_date,
                s3_url,
                total_score,
                feedback,
                topic,
                difficulty,
                focus
            )
        )
    
    query = """
                    UPDATE user_goals
                    SET total_user_taken_interviews = total_user_taken_interviews + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND role = %s;
                """
    cursor_for_goal_table.execute(query, (user_id, topic))
    conn.commit()
    cursor.close()
    cursor_for_goal_table.close()
    conn.close()
    return jsonify({"message": "Interview results stored successfully"}), 200


# Save Interview Transcript and Upload to S3
def save_transcript_to_s3(transcript, score, feedback, interview_details_data):
    interview_id = str(uuid.uuid4())
    interview_details_data = json.loads(interview_details_data)
    transcript_data = {
        "interview_id": interview_id,
        "timestamp": str(datetime.now()),
        "transcript": transcript,
        "score": score,
        "feedback": feedback
    }
    file_key = f"interview_transcripts/interview_{interview_id}.json"
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=file_key,
        Body=json.dumps(transcript_data),
        ContentType='application/json'
    )
    user_id = session.get('user_id') or getUniqueIdForUser(session.get('email'))
    s3_url = f"s3://{S3_BUCKET_NAME}/{file_key}"
    insert_into_redshift(interview_id, user_id, datetime.now(), s3_url, score, feedback, interview_details_data["topic"], interview_details_data["difficulty"], interview_details_data["focus"])
    return True



@app.route("/api/submit_simulation", methods=["POST"])
def submit_simulation():
    """
    API Endpoint: Submit Simulation
    -------------------------------
    Receives the user's answers for the interview simulation, processes them, and stores them in the database.

    Request Payload:
        {
            "answers": ["Answer 1", "Answer 2", ..., "Answer N"],
            "timestamp": "2024-11-24T15:30:00Z"
        }

    Returns:
        JSON response with success or failure message.
    """
    try:
        # Parse the JSON request payload
        data = request.get_json()
        answers = data.get("answers")
        timestamp = data.get("timestamp")

        # Validate the answers
        if not answers or len(answers) == 0:
            return jsonify({"success": False, "message": "No answers provided."}), 400

        # Process and store the simulation data (e.g., save to database or file)
        # Example: Store in a database
        # db.store_simulation(answers=answers, timestamp=timestamp)

        return jsonify({"success": True, "message": "Simulation submitted successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route("/history")
def history():
    # Example quiz history
    quiz_history_data = get_quiz_history()
    interview_history = fetch_interview_history()
    return render_template("history.html", quiz_history=quiz_history_data,interview_history=interview_history)


@app.route('/get_quiz_details/<quiz_id>', methods=['GET'])
def get_quiz_details(quiz_id):
    # Replace with actual logic to fetch quiz details from the database
    print(f"quiz_id",quiz_id)

    quiz_details = get_quiz_answers_for_quiz_id(quiz_id)
    # quiz_details = {
    #     "quizId": quiz_id,
    #     "questions": [
    #         {
    #             "question": "What is Python?",
    #             "correct_answer": "A programming language",
    #             "user_answer": "A snake",
    #             "explanation":"Python is a programming language"
    #         },
    #         {
    #             "question": "What is the output of 2+2?",
    #             "correct_answer": "4",
    #             "user_answer": "4"
    #         },
    #         {
    #             "question": "What is the output of 2+2?",
    #             "correct_answer": "4",
    #             "user_answer": "4"
    #         }
    #     ]
    # }

    return jsonify(quiz_details)


def get_quiz_answers_for_quiz_id(quiz_id):
            # Redshift connection
        conn = psycopg2.connect(
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD,
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT
        )
        cursor = conn.cursor()

        # Fetch quizzes for the user
        cursor.execute(
            """
            SELECT quiz_details
            FROM quiz_history
            WHERE quiz_id = %s
            ORDER BY quiz_date DESC
            """,
            (quiz_id,)
        )

        cursor_result = cursor.fetchone()[0]
        conn.close()
        # Convert the string into a Python list of dictionaries
        quiz_details_list = json.loads(cursor_result)
        # Check if the result is still a string
        if isinstance(quiz_details_list, str):
            # Deserialize again
            quiz_details_list = json.loads(quiz_details_list)

        # Transform into the desired structure
        transformed_data = {
            "quizId": quiz_id,  # Replace with the actual quiz_id if available
            "questions": []
        }
        # Iterate through the list to format each question
        print(f"quiz_details_list",quiz_details_list)
        print(f"quizID",quiz_id)
        for question_entry in quiz_details_list:
            transformed_data["questions"].append({
                "question": question_entry["question"],
                "correct_answer": question_entry["correct_answer"],
                "user_answer": question_entry["user_answer"],
                "explanation": question_entry.get("explanation", "No explanation available")
            })
        return transformed_data


@app.route('/submit_quiz_results', methods=['POST'])
def submit_quiz_results():
    try:
        # Get data from request
        data = request.json
        quiz_id = data['quiz_id']
        topic = data['topic']
        difficulty = data['difficulty']
        total_score = data['total_score']
        quiz_date = data['quiz_date']
        quiz_details = json.dumps(data['quiz_details'])  # Convert Python dict to JSON string

        # Redshift connection
        conn = psycopg2.connect(
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD,
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT
        )
        cursor_for_quiz_table = conn.cursor()
        cursor_for_goal_table = conn.cursor()
        user_id = session.get('user_id') or getUniqueIdForUser(session.get('email'))
        # Insert into Redshift
        cursor_for_quiz_table.execute(
            """
            INSERT INTO quiz_history (
                user_id, 
                quiz_id, 
                topic, 
                difficulty, 
                total_score, 
                quiz_date, 
                quiz_details
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,  # Assuming user_id is stored in session
                quiz_id,
                topic,
                difficulty,
                total_score,
                quiz_date,
                quiz_details
            )
        )

        query = """
                    UPDATE user_goals
                    SET total_user_taken_quizes = total_user_taken_quizes + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND role = %s;
                """
        cursor_for_goal_table.execute(query, (user_id, topic))

        conn.commit()
        cursor_for_quiz_table.close()
        cursor_for_goal_table.close()
        conn.close()

        return jsonify({"message": "Quiz results stored successfully"}), 200

    except Exception as e:
        print("Error storing quiz results:", str(e))
        return jsonify({"error": str(e)}), 500
    

@app.route('/get_quiz_history', methods=['GET'])
def get_quiz_history():
    try:
        user_id = session.get('user_id') or getUniqueIdForUser(session.get('email'))


        # Redshift connection
        conn = psycopg2.connect(
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD,
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT
        )
        cursor = conn.cursor()

        # Fetch quizzes for the user
        cursor.execute(
            """
            SELECT quiz_id, topic, difficulty, total_score, quiz_date
            FROM quiz_history
            WHERE user_id = %s
            ORDER BY quiz_date DESC
            """,
            (user_id,)
        )

        quizzes = cursor.fetchall()
        conn.close()

        quiz_history = [
            {
                "topic": row[1],
                "children": [
                    {
                    "difficulty": row[2],
                    "score": row[3],
                    "date": row[4],
                    "quizId": row[0],
                    }
                ]
            }
            for row in quizzes
        ]
        return quiz_history

    except Exception as e:
        print("Error fetching quiz history:", str(e))
        return jsonify({"error": str(e)}), 500
    
@app.template_filter('datetimeformat')
def datetimeformat(value):
    if isinstance(value, datetime):  # Check if value is a datetime object
        return value.strftime("%d-%b-%Y %H:%M")
    return value  # Return the original value if it's not a datetime object


def get_s3_url_for_interview_id(interview_id):
    conn = psycopg2.connect(
                host=REDSHIFT_HOST,
                port=REDSHIFT_PORT,
                dbname=REDSHIFT_DB,
                user=REDSHIFT_USER,
                password=REDSHIFT_PASSWORD
            )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interview_history WHERE interview_id = %s", (interview_id,))
    user_interview_record = cursor.fetchone()
    cursor.close()
    conn.close()
    return user_interview_record[3]

def fetch_interview_history():
    user_id = session.get('user_id') or getUniqueIdForUser(session.get('email'))
    # Replace this with a query to your Redshift table
            # Connect to Redshift
    conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interview_history WHERE user_id = %s", (user_id,))
    user_interview_records = cursor.fetchall()
    cursor.close()
    conn.close()
    interview_history = [
            {
                "interview_id":row[0],
                "user_id": row[1],
                "interview_date": row[2],
                "s3_url": row[3],
                "score": row[4],
                "feedback": row[5],
            }
            for row in user_interview_records
        ]
    return interview_history

@app.route("/get_transcript/<interview_id>")
def get_transcript(interview_id):
    transcript_url = get_s3_url_for_interview_id(interview_id)
    print(f"transcript_url",transcript_url)
    if transcript_url:
        s3_object = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key= transcript_url.split('/')[-2] + "/" +transcript_url.split('/')[-1])
        transcript_data = json.loads(s3_object['Body'].read().decode('utf-8'))
        print(f"transcript_data",transcript_data)
        return jsonify(transcript_data)
    return jsonify({"error": "Transcript not found"}), 404



@app.route('/learn_skills')
def learn_skills():
    skills = [
        {"id": "python_basics", "name": "Python Basics", "description": "Learn Python fundamentals."},
        {"id": "data_structures", "name": "Data Structures", "description": "Master common data structures."},
        {"id": "behavioral_skills", "name": "Behavioral Skills", "description": "Improve your communication skills."},
    ]
    return render_template('skills.html',name=session.get('name', 'User'), skills=skills)


@app.route('/set_goals', methods=['GET', 'POST'])
def set_goals():
    goal_history = fetch_goals()
    return render_template('goals.html', goals = goal_history)  # Render the goal-setting page


@app.route('/create_goal', methods=['POST','GET'])
def create_goal():
    user_id = session.get('user_id') or getUniqueIdForUser(session.get('email'))
    # Get the logged-in user's ID
    goal_name = request.form.get('goal_name')
    role = request.form.get('role')
    deadline = request.form.get('deadline')
    result = get_timeline_based_on_deadline(deadline)
    result = json.loads(result)
    deadline = (
    "In a week" if deadline == "less_prep_time" else 
    "1 - 2 weeks" if deadline == "mid_prep_time" else 
    "More than 2 weeks"
    )

    conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
    cursor = conn.cursor()
    # Insert the new goal into the database
    query = """
    INSERT INTO user_goals (user_id, goal_name, deadline, role, total_interviews_to_be_taken, total_user_taken_interviews, total_quizes_to_be_taken, total_user_taken_quizes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    cursor.execute(query, (user_id, goal_name, deadline, role, result["total_interviews_to_be_taken"], result["total_user_taken_interviews"], result["total_quizes_to_be_taken"], result["total_user_taken_quizes"]))
    conn.commit()
    return redirect('/set_goals')


def get_timeline_based_on_deadline(deadline):
    match deadline:
        case "less_prep_time":
            return json.dumps({"total_interviews_to_be_taken":15, "total_user_taken_interviews":0, "total_quizes_to_be_taken": 20, "total_user_taken_quizes": 0})
        case "mid_prep_time":
            return json.dumps({"total_interviews_to_be_taken":10, "total_user_taken_interviews":0, "total_quizes_to_be_taken": 10, "total_user_taken_quizes": 0})
        case "more_prep_time":
            return json.dumps({"total_interviews_to_be_taken":10, "total_user_taken_interviews":0, "total_quizes_to_be_taken": 10, "total_user_taken_quizes": 0})


def fetch_goals():
    user_id = session.get('user_id') or getUniqueIdForUser(session.get('email'))
    query = """
    SELECT id, goal_name, deadline, total_user_taken_quizes, total_quizes_to_be_taken, total_user_taken_interviews, total_interviews_to_be_taken,
        round(cast(total_user_taken_quizes as decimal(2,0)) / cast(total_quizes_to_be_taken as decimal(2,0)) * 100) as quiz_percentage,
        round(cast(total_user_taken_interviews as decimal(2,0)) / cast(total_interviews_to_be_taken as decimal(2,0)) * 100) as interview_percentage,
 	    round(cast(total_user_taken_quizes + total_user_taken_interviews as decimal(2,0)) / cast(total_quizes_to_be_taken + total_interviews_to_be_taken as decimal(2,0)) * 100) as total_percentage
    FROM user_goals
    WHERE user_id = %s order by created_at DESC;
    """
    conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=REDSHIFT_PORT,
            dbname=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
    cursor = conn.cursor()
    cursor.execute(query, (user_id,))
    goals = cursor.fetchall()
    goals_history = [
            {
                "id": row[0],
                "name": row[1],
                "deadline": row[2],
                "total_user_taken_quizes": row[3],
                "total_quizes_to_be_taken": row[4],
                "total_user_taken_interviews": row[5],
                "total_interviews_to_be_taken": row[6],
                "quizzesProgress": row[7],
                "interviewsProgress": row[8],
                "progress": row[9],
            }
            for row in goals
        ]
    conn.close()
    print("goals_history",goals_history)
    return goals_history



@app.route('/skills/<skill_id>')
def skill_tutorial(skill_id):
    # Mock data for a skill
    skill_data = {
        "python_basics": {
            "name": "Python Basics",
            "description": "Master the fundamentals of Python programming.",
            "video_url": "https://www.youtube.com/embed/kqtD5dpn9C8",
            "takeaways": [
                "Understand Python syntax and data types.",
                "Learn how to write Python functions and loops.",
                "Explore basic file handling and error handling."
            ],
            "resources": [
                {"name": "Official Python Documentation", "link": "https://docs.python.org/3/"},
                {"name": "Python Crash Course Book", "link": "https://nostarch.com/pythoncrashcourse2e"}
            ]
        },
        "data_structures": {
            "name": "Data Structures",
            "description": "Understand and implement essential data structures.",
            "video_url": "https://www.youtube.com/embed/RBSGKlAvoiM",
            "takeaways": [
                "Learn about arrays, linked lists, stacks, and queues.",
                "Understand tree and graph structures with examples.",
                "Master searching, sorting, and hashing algorithms."
            ],
            "resources": [
                {"name": "GeeksforGeeks Data Structures Tutorial", "link": "https://www.geeksforgeeks.org/data-structures/"},
                {"name": "Introduction to Algorithms (CLRS)", "link": "https://mitpress.mit.edu/books/introduction-algorithms-third-edition"}
            ]
        },
        "behavioral_skills": {
            "name": "Behavioral Skills",
            "description": "Enhance your interpersonal and communication skills.",
            "video_url": "https://www.youtube.com/embed/4z7gDsSKUmU",
            "takeaways": [
                "Learn effective communication techniques.",
                "Understand the STAR method for answering behavioral interview questions.",
                "Master emotional intelligence and adaptability in workplace scenarios."
            ],
            "resources": [
                {"name": "Harvard Business Review: Emotional Intelligence", "link": "https://hbr.org/topic/emotional-intelligence"},
                {"name": "STAR Interview Method Guide", "link": "https://www.themuse.com/advice/star-interview-method"}
            ]
        }
        
        # Add other skills here...
    }

    skill = skill_data.get(skill_id, {})
    if not skill:
        return "Skill not found", 404

    return render_template('skill_tutorial.html', skill=skill)


if __name__ == '__main__':
    app.run(debug=True)
