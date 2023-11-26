from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai
import os
import logging
import time
import uvicorn
from starlette.background import BackgroundTasks

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# Ensure that the OPENAI_API_KEY is set in the environment variables.
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("The OPENAI_API_KEY environment variable must be set.")

client = openai.Client()

logger = logging.getLogger("uvicorn.error")

# Global variable to store the thread id
current_thread_id = None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.exception("Error in index endpoint")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

class RoverEngineerRequest(BaseModel):
    question: str

@app.post("/rover_engineer_request")
async def rover_engineer_request(data: RoverEngineerRequest):
    global current_thread_id
    try:
        user_question = data.question

        # If there's no current thread, create one
        if current_thread_id is None:
            thread = client.beta.threads.create()
            current_thread_id = thread.id
        else:
            thread = client.beta.threads.retrieve(thread_id=current_thread_id)

        # Add the user's question to the thread
        message = client.beta.threads.messages.create(
            thread_id=current_thread_id, role="user", content=user_question)

        # Run the AI assistant
        run = client.beta.threads.runs.create(
            thread_id=current_thread_id, assistant_id="asst_X6pCppPwljfx0SJwFfpyF1lS")

        # Wait for the run to complete
        for _ in range(120):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=current_thread_id, run_id=run.id)
            if run_status.status == 'completed':
                break
            time.sleep(0.5)

        # Retrieve all messages in the thread
        thread_messages = client.beta.threads.messages.list(current_thread_id)

        # Find the AI's response
        ai_response = None
        for msg in thread_messages.data:
            if msg.role == 'assistant':
                ai_response = msg.content[0].text.value
                break

        if ai_response:
            # Log the AI's response instead of creating a system message
            logger.info(f"AI Response: {ai_response}")
            return {'response': ai_response}

        return {'response': 'No response from the AI.'}
    except Exception as e:
        logger.exception("Error in rover_engineer_request endpoint")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")
    

# Comment out if wanting to deploy on MS Azure:
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)