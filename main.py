from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
import uvicorn
import asyncio
import json
from typing import List, Dict
from dotenv import load_dotenv

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

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in index endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        client_id = str(id(websocket))
        self.active_connections[client_id] = websocket
        return client_id

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_json(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await process_message(client_id, data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
        manager.disconnect(client_id)

async def process_message(client_id: str, message: str):
    try:
        # Create a thread for this conversation
        thread = client.beta.threads.create()
        
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        # Send stream start event
        await manager.send_json(client_id, {
            "type": "stream_start"
        })

        # Create run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Poll for updates
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                # Get the messages
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Get the last assistant message
                for msg in messages.data:
                    if msg.role == "assistant":
                        # Send the content
                        if msg.content and len(msg.content) > 0:
                            content = msg.content[0].text.value
                            await manager.send_json(client_id, {
                                "type": "stream_content",
                                "content": content
                            })
                        break
                break
                
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": f"Run ended with status: {run_status.status}"
                })
                break
                
            # Check if any file search was used
            steps = client.beta.threads.runs.steps.list(
                thread_id=thread.id,
                run_id=run.id
            )
            
            file_search_details = []
            for step in steps.data:
                if (hasattr(step, 'step_details') and 
                    step.step_details.type == "tool_calls"):
                    for tool_call in step.step_details.tool_calls:
                        if (tool_call.type == "file_search" and 
                            hasattr(tool_call, "file_search") and 
                            hasattr(tool_call.file_search, "results")):
                            for result in tool_call.file_search.results:
                                file_search_details.append({
                                    "file_name": result.file_name,
                                    "file_citation": result.file_citation
                                })
            
            if file_search_details:
                await manager.send_json(client_id, {
                    "type": "file_search_info",
                    "files": file_search_details
                })
            
            # Short delay before next check
            await asyncio.sleep(0.1)

        # Send stream end event
        await manager.send_json(client_id, {
            "type": "stream_end"
        })

    except Exception as e:
        logger.error(f"Error in process_message: {str(e)}")
        await manager.send_json(client_id, {
            "type": "error",
            "message": "An error occurred while processing your request."
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)