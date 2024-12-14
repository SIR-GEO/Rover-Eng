from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional, Union, AsyncGenerator
import os
import logging
import uvicorn
import asyncio
import json
from dotenv import load_dotenv
from typing_extensions import override
from openai import AssistantEventHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rover-engineer")

app = FastAPI(title="Classic Rover Engineer")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# Initialize OpenAI client
client = OpenAI()

# Use existing assistant ID
ASSISTANT_ID = "asst_X6pCppPwljfx0SJwFfpyF1lS"
if not ASSISTANT_ID:
    logger.error("Assistant ID not found")
    raise ValueError("The ASSISTANT_ID must be set.")

# Store active threads
active_threads = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in index endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
    
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

async def stream_chat_response(message: str, thread_id: str = None) -> AsyncGenerator[str, None]:
    try:
        # Use existing thread or create new one
        if thread_id and thread_id in active_threads:
            thread = active_threads[thread_id]
        else:
            thread = client.beta.threads.create()
            active_threads[thread.id] = thread
            
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        # Create and stream the run
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
            event_handler=EventHandler(),
        ) as stream:
            for event in stream:
                if event.event == "thread.message.delta":
                    if event.data.delta.content:
                        for content in event.data.delta.content:
                            if content.type == "text":
                                yield f"data: {json.dumps({'type': 'content', 'content': content.text.value})}\n\n"
                elif event.event == "thread.run.completed":
                    # Get file search results if any
                    steps = client.beta.threads.runs.steps.list(
                        thread_id=thread.id,
                        run_id=event.data.id
                    )
                    
                    file_search_details = []
                    for step in steps.data:
                        if step.type == "tool_calls":
                            for tool_call in step.step_details.tool_calls:
                                if tool_call.type == "retrieval":
                                    for citation in tool_call.retrieval.citations:
                                        file_search_details.append({
                                            "file_name": citation.file_path.split('/')[-1] if hasattr(citation, 'file_path') else "Document",
                                            "quote": citation.text if hasattr(citation, 'text') else ""
                                        })
                    
                    if file_search_details:
                        yield f"data: {json.dumps({'type': 'file_search', 'files': file_search_details})}\n\n"
                    
                    yield "data: {\"type\": \"done\", \"thread_id\": \"" + thread.id + "\"}\n\n"
                    break

    except Exception as e:
        logger.error(f"Error in stream_chat_response: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred while processing your request.'})}\n\n"

@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        stream_chat_response(request.message, request.thread_id),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)