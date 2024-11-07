from flask import Flask, request, jsonify, session, render_template
from uuid import uuid4
import requests
import json

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Server URL for the model
MODEL_URL = "https://14b7-2409-40f4-300b-4b62-4177-87a-78de-1eb.ngrok-free.app/v1/chat/completions"
# Function to call the chat model
def chat_with_model(user_input, conversation_history, stream=False):
    # Append the user input to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Prepare the payload with the specified parameters
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": conversation_history,
        "temperature": 0.8,
        "max_tokens": 100,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "top_p": 0.95,
        "min_p": 0.05,
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Send the POST request
        response = requests.post(MODEL_URL, json=payload, headers=headers, stream=stream)
        response.raise_for_status()

        # Process the response
        if stream:
            response_text = ""
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    response_text += chunk.decode('utf-8')
            model_reply = {"role": "assistant", "content": response_text.strip()}
        else:
            model_reply = response.json().get('choices', [{}])[0].get('message', {})

        if 'content' in model_reply:
            # Append model's reply to the conversation history
            conversation_history.append(model_reply)
            return model_reply['content']
        else:
            return "I'm having trouble understanding your request. Can you please rephrase it?"

    except requests.exceptions.RequestException as req_err:
        return f"An error occurred: {req_err}"

# Route to render the HTML page
@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = str(uuid4())  # Create a unique session ID
        session['conversation_history'] = [
            {"role": "system", "content": "You are Dr. Akshay Karthick, a compassionate and concise doctor. Respond to patient queries with empathy and warmth, using 1-2 complete sentences. Ask only 1-2 questions at a time to keep the conversation focused. Offer virtual medications when appropriate and suggest physical visits only in rare cases. If any questions apart from medical queries are asked, respond like 'I'm a doctor, I can't answer those questions.'"}
        ]
    return render_template('index.html')

# Route to handle chat messages
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    conversation_history = session.get('conversation_history', [])

    # Get the response from the chat model
    reply = chat_with_model(user_input, conversation_history)

    # Update the session conversation history
    session['conversation_history'] = conversation_history

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
