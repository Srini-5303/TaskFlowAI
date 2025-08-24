from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import ProjectPlanningAgents
import traceback
from fastapi.responses import StreamingResponse
import json
import time


app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the planning system
planner = ProjectPlanningAgents()

class ProjectRequest(BaseModel):
    project_statement: str

class ProjectResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None

@app.post("/api/generate-plan")
async def generate_plan(request: ProjectRequest):
    def generate_with_progress():
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'starting', 'agent': 'system', 'message': 'Initializing agents...'})}\n\n"
            time.sleep(0.5)
            
            # Initialize planner
            planner = ProjectPlanningAgents()
            
            # Initialize state
            initial_state = {
                "project_statement": request.project_statement,
                "tasks": [],
                "timeline_tasks": [],
                "dependency_tasks": [],
                "formatted_output": {},
                "current_agent": "",
                "errors": []
            }
            
            # Run planner agent
            yield f"data: {json.dumps({'status': 'running', 'agent': 'planner', 'message': 'Breaking down project into tasks...'})}\n\n"
            state = planner.planner_agent(initial_state)
            time.sleep(1)
            
            # Run timeline agent
            yield f"data: {json.dumps({'status': 'running', 'agent': 'timeline', 'message': 'Assigning durations and deadlines...'})}\n\n"
            state = planner.timeline_agent(state)
            time.sleep(1)
            
            # Run dependency agent
            yield f"data: {json.dumps({'status': 'running', 'agent': 'dependency', 'message': 'Analyzing task dependencies...'})}\n\n"
            state = planner.dependency_agent(state)
            time.sleep(1)
            
            # Run formatter agent
            yield f"data: {json.dumps({'status': 'running', 'agent': 'formatter', 'message': 'Converting to structured output formats...'})}\n\n"
            state = planner.formatter_agent(state)
            time.sleep(0.5)
            
            # Send final result
            yield f"data: {json.dumps({'status': 'completed', 'agent': 'system', 'message': 'Plan generation completed!', 'data': state})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'agent': 'system', 'message': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_with_progress(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)