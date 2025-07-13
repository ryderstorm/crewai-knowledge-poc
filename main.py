from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import glob
from pathlib import Path
from typing import List, Dict
import logging

# CrewAI imports
from crewai import Agent, Task, Crew, LLM
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.knowledge_config import KnowledgeConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="CrewAI Knowledge PoC", version="1.0.0")

# Request/Response models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    sources: List[str]

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
                backstory="""You are an expert knowledge analyst who excels at finding relevant information 
                from documentation and synthesizing comprehensive answers. You always mention which documents 
                or files you referenced when providing answers. When answering questions, you should explicitly 
                state which source files you found the information in.""",
                knowledge_sources=self.knowledge_sources,
                knowledge_config=knowledge_config,
                llm=llm,
                verbose=True
            )
            
            # Create static task with input templating
            query_task = Task(
                description="""
                Answer the following question using the available knowledge sources: {query}
                
                Important instructions:
                1. Provide a comprehensive answer based on the available documentation
                2. Always explicitly mention which source files (by filename) you used to answer the question
                3. If you reference multiple files, list them clearly
                4. If information is not available in the knowledge base, state this clearly
                5. Format your response as: [Answer content] 
                   
                   Sources used: [list of filenames]
                """,
                expected_output="A detailed answer with explicit mention of source files used",
                agent=knowledge_agent
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
        """Query the knowledge base and return response with sources"""
        try:
            if not self.crew:
                raise HTTPException(status_code=500, detail="Crew not initialized")
            
            # Execute the crew with input templating
            result = self.crew.kickoff(inputs={"query": query})
            
            # Extract response and attempt to parse sources
            response_text = str(result)
            sources = self._extract_sources_from_response(response_text)
            
            return {
                "response": response_text,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge: {e}")
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    
    def _extract_sources_from_response(self, response: str) -> List[str]:
        """Extract source file names from the agent's response"""
        sources = []
        
        try:
            # Look for common patterns where sources might be mentioned
            response_lower = response.lower()
            
            # Get list of available markdown files
            available_files = [f.name for f in self.knowledge_dir.glob("*.md")]
            
            # Check if any filenames are mentioned in the response
            for filename in available_files:
                if filename.lower() in response_lower or filename.replace('.md', '').lower() in response_lower:
                    if filename not in sources:
                        sources.append(filename)
            
            # If no sources found via filename matching, return all available files
            # (since the agent used the knowledge base)
            if not sources and available_files:
                # Look for explicit source mentions
                lines = response.split('\n')
                for line in lines:
                    if 'source' in line.lower() and any(ext in line.lower() for ext in ['.md', 'file']):
                        # Try to extract filenames from this line
                        for filename in available_files:
                            if filename.lower() in line.lower():
                                sources.append(filename)
                
                # Fallback: if knowledge was used but sources unclear, include note
                if not sources:
                    sources = ["[Source information not clearly specified in response]"]
            
        except Exception as e:
            logger.error(f"Error extracting sources: {e}")
            sources = ["[Error extracting source information]"]
        
        return sources
    
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
    
    Returns the AI agent's response along with source file references.
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Processing query: {request.query}")
        
        result = knowledge_manager.query_knowledge(request.query)
        
        return QueryResponse(
            response=result["response"],
            sources=result["sources"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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