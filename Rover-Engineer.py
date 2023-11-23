from flask import Flask, render_template, request, jsonify
import openai
from openai import OpenAI
import openai
import time

app = Flask(__name__)

# Initialize the OpenAI client with your API key
openai.api_key = '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'
client = openai.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rover_engineer_request', methods=['POST'])
def rover_engineer_request():
    data = request.json
    user_question = data['question']

    # Create a thread
    thread = client.beta.threads.create()

    # Add a message to the thread with the user's question
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_question
    )

    # Create a run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id="asst_X6pCppPwljfx0SJwFfpyF1lS"
    )

    # Polling for the run's completion
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        time.sleep(1)  # Wait for 1 second before polling again

    # Retrieve messages after the run is completed
    thread_messages = client.beta.threads.messages.list(thread.id)

    # Find and return the assistant's response
    for msg in thread_messages.data:
        if msg.role == 'assistant':
            return jsonify({'response': msg.content[0].text.value})

    return jsonify({'response': 'No response from the AI.'})

if __name__ == '__main__':
    app.run(debug=True)