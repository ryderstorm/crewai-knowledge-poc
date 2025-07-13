# CrewAI Framework Guide

## Overview
CrewAI is a cutting-edge framework for orchestrating role-playing, autonomous AI agents. By fostering collaborative intelligence, CrewAI empowers agents to work together seamlessly, tackling complex tasks.

## Key Concepts

### Agents
Agents are autonomous units programmed to perform tasks, make decisions, and communicate with other agents.

Properties:
- **Role**: Defines the agent's function within the crew
- **Goal**: The individual objective the agent aims to achieve  
- **Backstory**: Provides context for the agent's role and goal
- **LLM**: The language model that powers the agent

### Tasks
Tasks are specific assignments completed by agents.

Properties:
- **Description**: A clear, concise statement of what the task entails
- **Expected Output**: A detailed description of expected task output
- **Agent**: The agent responsible for the task

### Crews
A crew is a collaborative group of agents working together to achieve a set of tasks.

### Knowledge Sources
CrewAI's Knowledge feature allows agents to access external information:
- Text files
- PDF documents  
- CSV data
- JSON files
- Web content

## Installation
```bash
pip install crewai
```

## Basic Example
```python
from crewai import Agent, Task, Crew

# Create an agent
researcher = Agent(
    role='Researcher',
    goal='Find and summarize information about AI trends',
    backstory='Expert analyst with keen eye for emerging technologies'
)

# Create a task
research_task = Task(
    description='Research latest AI trends in 2024',
    expected_output='Summary of top 5 AI trends',
    agent=researcher
)

# Create a crew
crew = Crew(
    agents=[researcher],
    tasks=[research_task]
)

# Execute
result = crew.kickoff()
```