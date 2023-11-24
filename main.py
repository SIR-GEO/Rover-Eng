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
    try:
        user_question = data.question

        # Create the thread, message, and run synchronously
        thread = client.beta.threads.create()
        message = client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_question)
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id="asst_X6pCppPwljfx0SJwFfpyF1lS")

        # Use a synchronous loop with time.sleep()
        for _ in range(30):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id)
            if run_status.status == 'completed':
                break
            time.sleep(0.5)  # Sleep for 0.5 seconds

        thread_messages = client.beta.threads.messages.list(thread.id)

        for msg in thread_messages.data:
            if msg.role == 'assistant':
                return {'response': msg.content[0].text.value}

        return {'response': 'No response from the AI.'}

    except Exception as e:
        logger.exception("Error in rover_engineer_request endpoint")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")
    

# Comment out if wanting to deploy on MS Azure:
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
