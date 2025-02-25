from openai import OpenAI
import json
openai_client = OpenAI(api_key = "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")
message_history = [
    {'role': 'assistant', 'content': 'Thank you for joining the call. My name is Sandy, shall we start with the interview?'}, 
    {'role': 'user', 'content': 'Yes.'}, 
    {'role': 'assistant', 'content': 'I see that you have been denied the F1 visa twice before. Can you please explain why you believe you were denied previously and what has changed since then to increase your chances of approval this time?'}, 
                   {'role': 'user', 'content': 'I believe the reason why I was denied the visa before was because I was not able to. Explain myself well to the officer, and I was stuttering a lot, because of which I was denied the visa.'}, 
                   {'role': 'assistant', 'content': 'I understand. It is important to communicate effectively during the visa interview. Can you tell me why you think you were unable to explain yourself well during the previous visa interviews?'}, 
                   {'role': 'user', 'content': 'I think I was starting the note and I was bought a text done by myself, correctly.'}, 
    
    {'role': 'assistant', 'content': 'Thank you for joining the call. We have recorded all your responses and will come back to you with our response.'}, 
    {'role': 'system', 'content': 'You are a US F1 Visa Inteviewer. The candidate has been denied F1 visa twice. Based on the below conversation between assistant and user , Evaluate the User responses for the questions asked by the assistant based on clarity, relevance, and conciseness .\n Provide a score out of 100 and give specific feedback. \n Give the response as Object with overall_score which is a integer and feedback which is a string'}]
response = openai_client.chat.completions.create(
                model = "gpt-4o",
                messages = message_history
            )

result = response.choices[0].message.content
json_object = json.loads(result)
print(f"feedback",json_object)