"""
Multi-Agent Project Planning System using LangGraph
This system implements four specialized agents for project planning:
1. Planner Agent - Breaks down projects into tasks
2. Timeline Agent - Assigns durations and deadlines
3. Dependency Agent - Determines task dependencies
4. Formatter Agent - Converts to structured output formats
"""

from typing import Dict, List, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import json
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv

load_dotenv()

# Define the shared state structure
class ProjectState(TypedDict):
    project_statement: str
    tasks: List[Dict[str, Any]]
    timeline_tasks: List[Dict[str, Any]]
    dependency_tasks: List[Dict[str, Any]]
    formatted_output: Dict[str, Any]
    current_agent: str
    errors: List[str]

class ProjectPlanningAgents:
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        """Initialize the multi-agent system with LLM configuration."""
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for agent orchestration."""
        workflow = StateGraph(ProjectState)
        
        # Add nodes (agents)
        workflow.add_node("planner", self.planner_agent)
        workflow.add_node("timeline", self.timeline_agent)
        workflow.add_node("dependency", self.dependency_agent)
        workflow.add_node("formatter", self.formatter_agent)
        
        # Define the flow
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "timeline")
        workflow.add_edge("timeline", "dependency")
        workflow.add_edge("dependency", "formatter")
        workflow.add_edge("formatter", END)
        
        return workflow.compile()
    
    def planner_agent(self, state: ProjectState) -> ProjectState:
        """
        Planner Agent: Breaks the user's project input into modular sub-tasks.
        """
        print("Planner Agent: Breaking down project into tasks...")
        
        system_prompt = """You are a Project Planning Expert specializing in task decomposition.

Your role is to analyze a project statement and break it down into clear, actionable sub-tasks.

Guidelines:
1. Create 5-8 specific, actionable tasks
2. Each task should have a clear deliverable
3. Tasks should be atomic (can't be broken down further meaningfully)
4. Include both technical and non-technical tasks as needed
5. Consider testing, documentation, and deployment phases

Output Format: Return ONLY a JSON array of task objects with these fields:
[
    {
        "id": "task_1",
        "name": "Task Name",
        "description": "Detailed description of what needs to be done",
        "category": "development|testing|documentation|deployment|planning",
        "estimated_complexity": "low|medium|high"
    }
]

Project Statement: {project_statement}
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Break down this project: {state['project_statement']}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            tasks = json.loads(content)
            
            return {
                **state,
                "tasks": tasks,
                "current_agent": "planner",
                "errors": []
            }
            
        except Exception as e:
            return {
                **state,
                "tasks": [],
                "current_agent": "planner",
                "errors": [f"Planner Agent Error: {str(e)}"]
            }
    
    def timeline_agent(self, state: ProjectState) -> ProjectState:
        """
        Timeline Agent: Assigns estimated durations and tentative deadlines to each task.
        """
        print("Timeline Agent: Assigning durations and deadlines...")
        
        system_prompt = """You are a Project Timeline Specialist focused on realistic time estimation.

Your role is to analyze tasks and assign realistic durations and deadlines.

Guidelines:
1. Consider task complexity when estimating duration
2. Add buffer time for testing and revisions
3. Account for realistic working hours (assume 6 productive hours/day)
4. Consider that complex tasks often take longer than expected
5. Set start dates assuming tasks run sequentially unless specified otherwise

Duration Guidelines:
- Low complexity: 0.5-2 days
- Medium complexity: 2-5 days  
- High complexity: 5-10 days

Output Format: Return ONLY a JSON array with the original task data plus timeline fields:
[
    {
        "id": "task_1",
        "name": "Task Name",
        "description": "Task description",
        "category": "category",
        "estimated_complexity": "complexity",
        "estimated_duration_days": 2.5,
        "start_date": "2024-01-15",
        "end_date": "2024-01-17",
        "buffer_days": 0.5
    }
]

Tasks to process: {tasks}
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Add timeline information to these tasks: {json.dumps(state['tasks'], indent=2)}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            timeline_tasks = json.loads(content)
            
            return {
                **state,
                "timeline_tasks": timeline_tasks,
                "current_agent": "timeline"
            }
            
        except Exception as e:
            return {
                **state,
                "timeline_tasks": state.get("tasks", []),
                "current_agent": "timeline",
                "errors": state.get("errors", []) + [f"Timeline Agent Error: {str(e)}"]
            }
    
    def dependency_agent(self, state: ProjectState) -> ProjectState:
        """
        Dependency Agent: Determines dependencies between tasks and establishes execution order.
        """
        print("Dependency Agent: Analyzing task dependencies...")
        
        system_prompt = """You are a Project Dependency Analyst specializing in task sequencing and relationships.

Your role is to analyze tasks and identify logical dependencies between them.

Guidelines:
1. Identify which tasks must be completed before others can start
2. Consider logical prerequisites (design before implementation, etc.)
3. Identify tasks that can run in parallel
4. Avoid circular dependencies
5. Consider resource constraints and knowledge dependencies
6. Update start/end dates based on dependencies

Dependency Types:
- "finish_to_start": Task B cannot start until Task A finishes
- "start_to_start": Task B cannot start until Task A starts
- "parallel": Tasks can run simultaneously

Output Format: Return ONLY a JSON array with tasks plus dependency information:
[
    {
        "id": "task_1",
        "name": "Task Name",
        "description": "Task description",
        "category": "category",
        "estimated_complexity": "complexity",
        "estimated_duration_days": 2.5,
        "start_date": "2024-01-15",
        "end_date": "2024-01-17",
        "buffer_days": 0.5,
        "dependencies": [
            {
                "depends_on": "task_id",
                "relationship": "finish_to_start",
                "description": "Why this dependency exists"
            }
        ],
        "priority": "high|medium|low",
        "can_parallel": ["task_2", "task_3"]
    }
]

Tasks with timeline: {timeline_tasks}
"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Analyze dependencies for these tasks: {json.dumps(state['timeline_tasks'], indent=2)}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            dependency_tasks = json.loads(content)
            
            return {
                **state,
                "dependency_tasks": dependency_tasks,
                "current_agent": "dependency"
            }
            
        except Exception as e:
            return {
                **state,
                "dependency_tasks": state.get("timeline_tasks", []),
                "current_agent": "dependency",
                "errors": state.get("errors", []) + [f"Dependency Agent Error: {str(e)}"]
            }
    
    def formatter_agent(self, state: ProjectState) -> ProjectState:
        """
        Formatter Agent: Converts structured output into Markdown, JSON, or Gantt chart syntax.
        """
        print("Formatter Agent: Converting to structured output formats...")
        
        try:
            tasks = state['dependency_tasks']
            
            # Generate multiple output formats
            formatted_output = {
                "json": tasks,
                "markdown": self._generate_markdown(tasks),
                "mermaid_gantt": self._generate_mermaid_gantt(tasks),
                "summary": self._generate_summary(tasks, state['project_statement'])
            }
            
            return {
                **state,
                "formatted_output": formatted_output,
                "current_agent": "formatter"
            }
            
        except Exception as e:
            return {
                **state,
                "formatted_output": {"error": f"Formatter Agent Error: {str(e)}"},
                "current_agent": "formatter",
                "errors": state.get("errors", []) + [f"Formatter Agent Error: {str(e)}"]
            }
    
    def _generate_markdown(self, tasks: List[Dict]) -> str:
        """Generate Markdown formatted project plan."""
        md = "# Project Plan\n\n"
        
        # Summary
        md += f"Total Tasks: {len(tasks)}\n"
        total_days = sum(task.get('estimated_duration_days', 0) for task in tasks)
        md += f"Estimated Duration: {total_days:.1f} days\n\n"
        
        # Tasks by category
        categories = {}
        for task in tasks:
            category = task.get('category', 'uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(task)
        
        for category, category_tasks in categories.items():
            md += f"## {category.title()}\n\n"
            for task in category_tasks:
                md += f"### {task['name']}\n"
                md += f"ID: {task['id']}\n"
                md += f"Description: {task['description']}\n"
                md += f"**Duration: {task.get('estimated_duration_days', 'N/A')} days\n"
                md += f"Complexity: {task.get('estimated_complexity', 'N/A')}\n"
                md += f"Priority: {task.get('priority', 'N/A')}\n"
                
                if task.get('dependencies'):
                    md += "Dependencies:\n"
                    for dep in task['dependencies']:
                        md += f"- {dep['depends_on']}: {dep['description']}\n"
                
                md += "\n"
        
        return md
    
    def _generate_mermaid_gantt(self, tasks: List[Dict]) -> str:
        """Generate Mermaid.js compatible Gantt chart syntax."""
        gantt = "gantt\n"
        gantt += "    title Project Timeline\n"
        gantt += "    dateFormat YYYY-MM-DD\n\n"
        
        # Group by category
        categories = {}
        for task in tasks:
            category = task.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(task)
        
        for category, category_tasks in categories.items():
            gantt += f"    section {category.title()}\n"
            for task in category_tasks:
                task_name = task['name'][:50]  # Limit length for readability
                start_date = task.get('start_date', '2024-01-01')
                duration = int(task.get('estimated_duration_days', 1))
                gantt += f"    {task_name} :{task['id']}, {start_date}, {duration}d\n"
        
        return gantt
    
    def _generate_summary(self, tasks: List[Dict], project_statement: str) -> Dict:
        """Generate project summary statistics."""
        categories = {}
        complexities = {"low": 0, "medium": 0, "high": 0}
        priorities = {"low": 0, "medium": 0, "high": 0}
        
        total_duration = 0
        
        for task in tasks:
            # Category distribution
            category = task.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1
            
            # Complexity distribution
            complexity = task.get('estimated_complexity', 'medium')
            complexities[complexity] = complexities.get(complexity, 0) + 1
            
            # Priority distribution
            priority = task.get('priority', 'medium')
            priorities[priority] = priorities.get(priority, 0) + 1
            
            # Duration
            total_duration += task.get('estimated_duration_days', 0)
        
        return {
            "project_statement": project_statement,
            "total_tasks": len(tasks),
            "estimated_duration_days": round(total_duration, 1),
            "category_distribution": categories,
            "complexity_distribution": complexities,
            "priority_distribution": priorities
        }
    
    def run_planning_pipeline(self, project_statement: str) -> Dict[str, Any]:
        """
        Execute the complete multi-agent planning pipeline.
        
        Args:
            project_statement: The project description to be planned
            
        Returns:
            Complete planning output from all agents
        """
        print(f"Starting multi-agent project planning for: {project_statement}...")
        print("=" * 80)
        
        # Initialize state
        initial_state = {
            "project_statement": project_statement,
            "tasks": [],
            "timeline_tasks": [],
            "dependency_tasks": [],
            "formatted_output": {},
            "current_agent": "",
            "errors": []
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        print("=" * 80)
        print("Multi-agent planning pipeline completed!")
        
        if result.get("errors"):
            print("Errors encountered:")
            for error in result["errors"]:
                print(f"   - {error}")
        
        return result
