from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import openai
import time
import keychain

app = FastAPI()
templates = Jinja2Templates(directory="templates")

import os
openai.api_key = os.environ.get('OPENAI_API_KEY')

client = openai.Client()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RoverEngineerRequest(BaseModel):
    question: str

@app.post("/rover_engineer_request")
async def rover_engineer_request(data: RoverEngineerRequest):
    try:
        user_question = data.question

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
        for _ in range(30):  # Poll for up to 30 seconds
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            time.sleep(1)

        # Retrieve messages after the run is completed
        thread_messages = client.beta.threads.messages.list(thread.id)

        # Find and return the assistant's response
        for msg in thread_messages.data:
            if msg.role == 'assistant':
                return {'response': msg.content[0].text.value}

        return {'response': 'No response from the AI.'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
