from flask import Flask, request, jsonify, render_template
import requests
import json

app = Flask(__name__)

# Server URL for the model
MODEL_URL = "http://127.0.0.1:1234/v1/chat/completions"

# Initialize conversation history with specific doctor attributes
conversation_history = [
    {"role": "system", "content": "You are Dr. Akshay Karthick, a compassionate and concise doctor. Respond to patient queries with empathy and warmth, using 1-2 complete sentences. Ask only 1-2 questions at a time to keep the conversation focused. Offer virtual medications when appropriate and suggest physical visits only in rare cases."}
]

# Function to call the chat model with specified parameters
def chat_with_model(user_input, stream=False):
    # Append the user input to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Prepare the payload with the specified parameters
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": conversation_history,
        "temperature": 0.8,                # Set temperature to 0.8
        "max_tokens": 100,                 # Set maximum response length to 100 tokens
        "top_k": 40,                       # Set top-k sampling to 40
        "repeat_penalty": 1.1,             # Set repeat penalty to 1.1
        "top_p": 0.95,                     # Set top-p sampling to 0.95
        "min_p": 0.05,                     # Set minimum p sampling to 0.05
        "stream": stream
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Send the POST request
        response = requests.post(MODEL_URL, json=payload, headers=headers, stream=stream)
        response.raise_for_status()  # Check for request errors

        # If streaming, accumulate the response
        if stream:
            response_text = ""
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    response_text += chunk.decode('utf-8')
            model_reply = {"role": "assistant", "content": response_text.strip()}
        else:
            model_reply = response.json().get('choices', [{}])[0].get('message', {})

        # Ensure the model's reply is valid
        if 'content' in model_reply:
            # Append model's reply to the conversation history
            conversation_history.append(model_reply)
            return model_reply['content']
        else:
            return "I'm having trouble understanding your request. Can you please rephrase it?"

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.ConnectionError:
        return "Connection error. Please check if the server is running."
    except requests.exceptions.Timeout:
        return "Request timed out. Please try again."
    except requests.exceptions.RequestException as req_err:
        return f"An error occurred: {req_err}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    reply = chat_with_model(user_input)
    return jsonify({'reply': reply})

if __name__ == "__main__":
    app.run(debug=True)
