
CREATE TABLE user_profile_data (
    user_id bigint identity(1, 1),               -- Auto-incrementing unique ID
    name VARCHAR(150) NOT NULL,          -- Full name of the user
    email VARCHAR(150) UNIQUE NOT NULL,  -- Email address (must be unique)
    phone VARCHAR(15),                   -- Phone number
    job_title VARCHAR(100),              -- Current job title
    experience VARCHAR(10),              -- Experience range (e.g., 1-3, 3-5)
    industry VARCHAR(100),               -- Industry of the user
    role VARCHAR(100),                   -- Job role the user is preparing for
    skills TEXT,                         -- Skills of the user
    interests TEXT,                      -- Interests of the user
    focus TEXT,                          -- Area of focus
    qualification VARCHAR(100),          -- Qualification of the user
    field_of_study VARCHAR(100),         -- Field of study
    university VARCHAR(100),             -- University name
    certifications TEXT,                 -- Certifications the user holds
    resume_url VARCHAR(255),             -- URL of the uploaded resume
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
  	primary key(user_id)
);


CREATE TABLE interview_history (
    interview_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    interview_date TIMESTAMP,
    s3_url VARCHAR(max),
    score INT,
    feedback VARCHAR(max)
);

CREATE TABLE quiz_history (
    id bigint identity(1, 1),
    user_id VARCHAR(255) NOT NULL,    -- User who took the quiz
    quiz_id  Varchar(max) NOT NULL,          -- Unique identifier for the quiz
    topic VARCHAR(255) NOT NULL,    -- Topic of the quiz
    difficulty VARCHAR(50) NOT NULL,-- Difficulty level (Easy/Medium/Hard)
    total_score INT NOT NULL,       -- Total score of the quiz
    quiz_date TIMESTAMP NOT NULL,   -- Date and time of the quiz
    quiz_details SUPER NOT NULL,     -- JSON object with questions, answers, etc. with fields as  question,correct_answer , user_answer, explanation, is_correct
    primary key(id)
);



CREATE TABLE user_goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    goal_name VARCHAR(255) NOT NULL,
    deadline DATE NOT NULL,
    role VARCHAR(100) NOT NULL,
    total_interviews_to_be_taken INT NOT NULL,
    total_user_taken_interviews INT DEFAULT 0,
    total_quizes_to_be_taken INT NOT NULL,
    total_user_taken_quizes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);


select * from interview_history
alter table user_profile_data add column unique_id varchar(255)
select * from user_profile_data
--drop table quiz_history

select * from quiz_history