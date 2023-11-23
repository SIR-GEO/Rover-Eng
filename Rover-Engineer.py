from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serving static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Hardcoded API key and Assistant ID
API_KEY = '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'
ASSISTANT_ID = 'asst_X6pCppPwljfx0SJwFfpyF1lS'

def send_message_to_assistant(assistant_id, message):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'OpenAI-Beta': 'assistants=v1'  # Include this if you're using beta features
    }
    data = {
           'input': {
               'messages': [{'role': 'user', 'content': message}]
           }
    }
    logger.info(f'Sending message to assistant: {message}')
    response = requests.post(f'https://api.openai.com/v1/assistants/{assistant_id}/messages', headers=headers, json=data)
    logger.info(f'OpenAI API Response Status Code: {response.status_code}')
    logger.info(f'OpenAI API Response: {response.json()}')
    return response

@app.post('/rover_engineer_request')
async def handle_rover_engineer_ai_request(request: Request):
    try:
        body = await request.json()
        question = body.get('question', '')
        if not question:
            return JSONResponse(content={"response": "Question is empty"}, status_code=400)

        response = send_message_to_assistant(ASSISTANT_ID, question)
        
        if response.status_code == 200:
            response_data = response.json().get('choices', [])
            if response_data:
                return JSONResponse(content={"response": response_data[0]['message']['content']})
            else:
                return JSONResponse(content={"response": "Unexpected response structure"}, status_code=500)
        else:
            logger.error(f'OpenAI Error: {response.status_code} {response.text}')
            return JSONResponse(content={"response": f"OpenAI Error: {response.text}"}, status_code=response.status_code)
    except Exception as e:
        logger.exception("An error occurred while processing the request.")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
