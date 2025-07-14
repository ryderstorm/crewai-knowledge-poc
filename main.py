from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
# CrewAI imports
from crewai import Agent, Task, Crew, LLM
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.knowledge_config import KnowledgeConfig

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="CrewAI Knowledge PoC", version="1.0.0")

# Request/Response models
class AgentResponse(BaseModel):
    response: str
    sources: List[str]
    found_relevant_sources: bool

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    status: str  # 'success' or 'error'
    response: str  # The actual response content
    sources: List[str]  # List of source files used
    found_relevant_sources: bool
    metadata: dict = {}  # Additional metadata about the response
    error: Optional[dict] = None  # Error details if status is 'error'

class KnowledgeManager:
    """Manages knowledge sources and CrewAI setup"""

    def __init__(self, knowledge_dir: str = "./knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_sources = []
        self.crew = None
        self._setup_knowledge()
        self._setup_crew()

    def _setup_knowledge(self):
        """Load all markdown files from knowledge directory"""
        try:
            # Ensure knowledge directory exists
            self.knowledge_dir.mkdir(exist_ok=True)

            # Find all markdown files
            md_files = list(self.knowledge_dir.glob("*.md"))

            if not md_files:
                logger.warning(f"No .md files found in {self.knowledge_dir}")
                return

            # Create knowledge sources for each file
            for md_file in md_files:
                try:
                    # Use relative path from knowledge directory
                    relative_path = md_file.name

                    knowledge_source = TextFileKnowledgeSource(
                        file_paths=[relative_path],
                        metadata={"source_file": str(md_file.name)}
                    )
                    self.knowledge_sources.append(knowledge_source)
                    logger.info(f"Added knowledge source: {md_file.name}")

                except Exception as e:
                    logger.error(f"Error loading {md_file}: {e}")

        except Exception as e:
            logger.error(f"Error setting up knowledge: {e}")

    def _setup_crew(self):
        """Initialize CrewAI crew with knowledge-enabled agent"""
        try:
            # Configure LLM (using OpenAI as default, can be changed)
            llm = LLM(model="gpt-4o-mini", temperature=0.1)

            # Knowledge configuration for better results
            knowledge_config = KnowledgeConfig(
                results_limit=5,  # Return top 5 relevant chunks
                score_threshold=0.3  # Lower threshold for more inclusive results
            )

            # Create knowledge synthesis agent
            knowledge_agent = Agent(
                role="Knowledge Synthesizer",
                goal="Provide accurate answers based on the available knowledge base, always citing the source files used",
                backstory="You are an expert knowledge analyst who excels at finding relevant information from documentation and synthesizing comprehensive answers.",
                knowledge_sources=self.knowledge_sources,
                knowledge_config=knowledge_config,
                llm=llm,
                verbose=True
            )

            # Create static task with input templating
            query_task = Task(
                description="""
                Answer the following question using only the available knowledge sources: {query}

                Guidelines for your response:
                1. The response MUST be based SOLELY on the provided knowledge sources
                2. If the knowledge sources contain relevant information:
                   - Provide a comprehensive answer
                   - List EXACT source filenames that were used
                   - Be specific about which information came from which source
                3. If the knowledge sources DO NOT contain relevant information:
                   - State clearly that no relevant information was found
                   - Do NOT attempt to answer the question
                   - Do NOT list any sources in the 'sources' field
                4. Never make up or guess information that's not in the knowledge sources
                5. If you are unsure, say you do not know rather than guessing
                """,
                expected_output="A response based strictly on the provided knowledge sources.",
                agent=knowledge_agent,
                output_pydantic=AgentResponse
            )

            # Create a reusable crew
            self.crew = Crew(
                agents=[knowledge_agent],
                tasks=[query_task],
                verbose=False,
                knowledge_sources=self.knowledge_sources  # Also add at crew level
            )

            logger.info("CrewAI crew initialized successfully")

        except Exception as e:
            logger.error(f"Error setting up crew: {e}")
            raise

    def query_knowledge(self, query: str) -> Dict[str, any]:
        """
        Query the knowledge base and return a consistent JSON response with sources.

        Args:
            query: The user's query string

        Returns:
            A dictionary with the following structure:
            {
                'status': 'success' or 'error',
                'response': str,    # The response content
                'sources': List[str],  # Source files used
                'metadata': dict,   # Additional metadata
                'error': dict or None  # Error details if status is 'error'
            }
        """
        import uuid
        from datetime import datetime

        # Initialize response with common fields
        response = {
            'status': 'success',
            'response': '',
            'found_relevant_sources': False,
            'sources': [],
            'metadata': {
                'query': query,
                'knowledge_files_count': len(self.get_available_files())
            },
            'error': None
        }

        try:
            if not self.crew:
                raise HTTPException(status_code=500, detail="Crew not initialized")

            # Execute the crew with input templating
            result = self.crew.kickoff(inputs={"query": query})

            # Extract response and sources
            response_text = result.pydantic.response
            raw_response = result.raw
            logger.debug(f"Raw response: {raw_response}")
            sources = result.pydantic.sources
            sources_found = result.pydantic.found_relevant_sources
            token_usage = result.token_usage

            # Update response with successful data
            response.update({
                'response': response_text,
                'sources': sources,
                'found_relevant_sources': sources_found,
                'metadata': {
                    **response['metadata'],
                    'raw_response': raw_response,
                    'response_length': len(response_text),
                    'token_usage': token_usage
                }
            })

        except Exception as e:
            error_id = str(uuid.uuid4())
            error_msg = str(e)
            logger.error(f"Error {error_id} in query_knowledge: {error_msg}", exc_info=True)

            response.update({
                'status': 'error',
                'error': {
                    'id': error_id,
                    'type': e.__class__.__name__,
                    'message': error_msg,
                    'code': 500 if not isinstance(e, (ValueError, RuntimeError)) else 400
                }
            })

            # For HTTP exceptions, include the status code
            if hasattr(e, 'status_code'):
                response['error']['code'] = e.status_code

        return response


    def get_available_files(self) -> List[str]:
        """Get list of available knowledge files"""
        try:
            return [f.name for f in self.knowledge_dir.glob("*.md")]
        except Exception as e:
            logger.error(f"Error getting available files: {e}")
            return []

# Initialize knowledge manager
knowledge_manager = KnowledgeManager()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    available_files = knowledge_manager.get_available_files()
    return {
        "message": "CrewAI Knowledge PoC API",
        "version": "1.0.0",
        "available_files": available_files,
        "endpoints": {
            "POST /query": "Submit a query to the knowledge base",
            "GET /health": "Health check endpoint",
            "GET /files": "List available knowledge files"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """
    Query the knowledge base with a user question.

    Returns a consistent JSON response with the AI agent's response and source file references.

    Response format:
    {
        'status': 'success' or 'error',
        'response': str,    # The response content
        'sources': List[str],  # Source files used
        'metadata': dict,   # Additional metadata about the query
        'error': dict or None  # Error details if status is 'error'
    }
    """
    try:
        # Delegate to the knowledge manager which now handles all error cases
        result = knowledge_manager.query_knowledge(request.query)

        # If there was an error in the knowledge manager, raise appropriate HTTP exception
        if result['status'] == 'error' and 'error' in result:
            error = result['error']
            raise HTTPException(
                status_code=error.get('code', 500),
                detail={
                    'error_id': error.get('id', 'unknown'),
                    'message': error.get('message', 'An unknown error occurred'),
                    'type': error.get('type', 'UnknownError')
                }
            )

        return QueryResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        # Handle any unexpected errors
        error_id = str(uuid.uuid4())
        logger.error(f"Unexpected error {error_id} in query endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                'error_id': error_id,
                'message': 'An unexpected error occurred',
                'type': 'UnexpectedError'
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    available_files = knowledge_manager.get_available_files()
    return {
        "status": "healthy",
        "knowledge_files_count": len(available_files),
        "crew_initialized": knowledge_manager.crew is not None
    }

@app.get("/files")
async def list_files():
    """List all available knowledge files"""
    try:
        files = knowledge_manager.get_available_files()
        return {
            "available_files": files,
            "count": len(files),
            "knowledge_directory": str(knowledge_manager.knowledge_dir)
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving file list")

if __name__ == "__main__":
    import uvicorn

    # Check for required environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Please set these environment variables before running the application.")
        exit(1)

    print("Starting FastAPI + CrewAI Knowledge PoC...")
    print("Available endpoints:")
    print("  POST http://localhost:8000/query - Submit queries")
    print("  GET  http://localhost:8000/files - List knowledge files")
    print("  GET  http://localhost:8000/health - Health check")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
