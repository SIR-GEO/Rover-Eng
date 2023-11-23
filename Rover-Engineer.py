from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

app = FastAPI()

# Serving static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Hardcoded API key and Assistant ID
API_KEY = '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'
ASSISTANT_ID = 'asst_X6pCppPwljfx0SJwFfpyF1lS'

def create_openai_thread():
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'OpenAI-Beta': 'assistants=v1'
    }
    response = requests.post('https://api.openai.com/v1/threads', headers=headers, json={})
    
    if response.status_code == 200:
        thread_id = response.json().get('id')
        if thread_id:
            return thread_id
        else:
            app.logger.error('No thread ID in the response')
            return None
    else:
        app.logger.error(f'Failed to create OpenAI thread: {response.status_code} {response.text}')
        return None

def get_current_thread_id():
    return create_openai_thread()

def send_message_to_thread(thread_id, message):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'OpenAI-Beta': 'assistants=v1'
    }
    data = {
        'role': 'user',
        'content': message
    }
    response = requests.post(f'https://api.openai.com/v1/threads/{thread_id}/messages', headers=headers, json=data)
    app.logger.info(f'OpenAI API Response: {response.json()}')
    return response

@app.post('/rover_engineer_request')
async def handle_rover_engineer_ai_request(request: Request):
    body = await request.json()
    question = body.get('question', '')
    if not question:
        return JSONResponse(content={"response": "Question is empty"})

    current_thread_id = get_current_thread_id()
    if not current_thread_id:
        return JSONResponse(content={"response": "Failed to get thread ID"})

    response = send_message_to_thread(current_thread_id, question)
    
    if response.status_code == 200:
        response_data = response.json().get('data', [])
        if response_data and 'text' in response_data[0]['content']:
            return JSONResponse(content={"response": response_data[0]['content']['text']['value']})
        else:
            return JSONResponse(content={"response": "Unexpected response structure"})
    else:
        app.logger.error(f'cURL Error: {response.text}')
        return JSONResponse(content={"response": f"cURL Error: {response.text}"})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
