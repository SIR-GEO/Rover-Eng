from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import openai
import asyncio
import os
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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

        # Assuming that the OpenAI client has asynchronous methods.
        thread = await client.beta.threads.create()
        message = await client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_question)

        run = await client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id="asst_X6pCppPwljfx0SJwFfpyF1lS")

        for _ in range(30):
            run_status = await client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id)
            if run_status.status == 'completed':
                break
            await asyncio.sleep(1)

        thread_messages = await client.beta.threads.messages.list(thread.id)

        for msg in thread_messages.data:
            if msg.role == 'assistant':
                return {'response': msg.content[0].text.value}

        return {'response': 'No response from the AI.'}

    except Exception as e:
        logger.exception("Error in rover_engineer_request endpoint")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")