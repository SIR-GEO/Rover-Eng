from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
@app.route('/')
def index():
    return open('index.html').read()
# Environment variables for API key and Assistant ID
API_KEY = os.environ.get('OPENAI_API_KEY', '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')
ASSISTANT_ID = os.environ.get('OPENAI_ASSISTANT_ID', 'asst_X6pCppPwljfx0SJwFfpyF1lS')

def create_openai_thread():
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.post('https://api.openai.com/v1/threads', headers=headers, json={})
    
    if response.status_code == 200:
        return response.json().get('id')
    else:
        app.logger.error(f'Failed to create OpenAI thread: {response.text}')
        return None

def get_current_thread_id():
    # Ideally, you would use a database or persistent storage to save the thread ID
    # For simplicity, this example creates a new thread every time
    return create_openai_thread()

@app.route('/rover_engineer_request', methods=['POST'])
def handle_rover_engineer_ai_request():
    question = request.form.get('question', '')
    if not question:
        return jsonify({"response": "Question is empty"})

    current_thread_id = get_current_thread_id()
    if not current_thread_id:
        return jsonify({"response": "Failed to get thread ID"})

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'OpenAI-Beta': 'assistants=v1'
    }
    data = {
        'content': question
    }
    response = requests.post(f'https://api.openai.com/v1/threads/{current_thread_id}/messages', headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json().get('data', [])
        if response_data and 'text' in response_data[0]['content']:
            return jsonify({"response": response_data[0]['content']['text']['value']})
        else:
            return jsonify({"response": "Unexpected response structure"})
    else:
        app.logger.error(f'cURL Error: {response.text}')
        return jsonify({"response": f"cURL Error: {response.text}"})

if __name__ == '__main__':
    app.run()
