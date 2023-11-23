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
openai.api_key = os.environ.get('OPENAI_API_KEY')
client = openai.Client()

logger = logging.getLogger("uvicorn.error")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in index endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RoverEngineerRequest(BaseModel):
    question: str

@app.post("/rover_engineer_request")
async def rover_engineer_request(data: RoverEngineerRequest):
    try:
        user_question = data.question

        thread = client.beta.threads.create()
        message = client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_question)

        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id="asst_X6pCppPwljfx0SJwFfpyF1lS")

        for _ in range(30):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id)
            if run_status.status == 'completed':
                break
            await asyncio.sleep(1)

        thread_messages = client.beta.threads.messages.list(thread.id)

        for msg in thread_messages.data:
            if msg.role == 'assistant':
                return {'response': msg.content[0].text.value}

        return {'response': 'No response from the AI.'}

    except Exception as e:
        logger.error(f"Error in rover_engineer_request endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
