# FastAPI + CrewAI Knowledge PoC

A proof-of-concept application that demonstrates integration between FastAPI and CrewAI's Knowledge feature. This application processes markdown files from a local folder into CrewAI Knowledge and provides a REST API for querying the knowledge base with AI-powered responses and source attribution.

## Features

- 🚀 **FastAPI REST API** - Clean, fast API with automatic documentation
- 🤖 **CrewAI Knowledge Integration** - Leverages CrewAI's latest Knowledge feature
- 📚 **Markdown Knowledge Base** - Processes all `.md` files from `./knowledge/` directory  
- 🔍 **Source Attribution** - Attempts to track which files contributed to responses
- ⚡ **Real-time Processing** - Query knowledge base instantly via API
- 📖 **Automatic Documentation** - Interactive API docs at `/docs`

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [just](https://just.systems/) command runner (for project tasks)
- OpenAI API key (or other LLM provider)

### Installation

1. **Install just command runner:**
```bashv
# macOS
brew install just

# Other platforms: https://just.systems/
```

2. **Clone or download the project:**
```bash
git clone <repository-url>
cd fastapi-crewai-poc
```

All necessary files are included in the repository:
- `main.py` - FastAPI application
- `pyproject.toml` - Project configuration
- `justfile` - Task automation
- `test_api.py` - Test suite
- `.env.template` - Environment template
- `.gitignore` - Git ignore rules
- `knowledge/` - Sample markdown files

3. **Set up the project:**
```bash
just setup
```

This will:
- Check all requirements (Python 3.11+, uv, just)
- Install dependencies with uv
- Verify environment setup

4. **Configure environment:**
```bash
just init-env  # Copy .env.template to .env
# Edit .env and add your OpenAI API key
```

### Knowledge Setup

The repository includes sample knowledge files in the `knowledge/` directory:
- `fastapi-guide.md` - FastAPI development best practices
- `crewai-guide.md` - CrewAI framework documentation  
- `ai-deployment.md` - AI application deployment guide

You can:
1. **Use the sample files** to test the system immediately
2. **Replace with your own** markdown files for your specific use case
3. **Add additional files** - any `.md` files in the knowledge directory will be automatically processed

To add your own knowledge:
```bash
# Remove sample files (optional)
rm knowledge/*.md

# Add your own markdown files
cp /path/to/your/docs/*.md knowledge/

# Restart the server to reload knowledge
just dev
```

### Running the Application

1. **Start the development server:**
```bash
just dev
```

2. **Access the application:**
- API Base URL: http://localhost:8000
- Interactive API Docs: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc

### Available Commands

```bash
# Development
just dev              # Start development server with hot reload
just start            # Start production server
just test             # Run comprehensive API tests
just test-interactive # Interactive testing mode

# Code Quality  
just format           # Format code with ruff
just lint             # Lint code with ruff
just lint-fix         # Lint and auto-fix issues
just check            # Run all quality checks

# API Testing
just health           # Quick health check
just files            # List knowledge files
just query "Your question here"  # Test a query

# Utilities
just clean            # Clean temporary files
just tree             # Show project structure
just help             # Show all commands
```

## API Usage

### Query the Knowledge Base

**Endpoint:** `POST /query`

**Request:**
```json
{
  "query": "What are the FastAPI best practices for API development?"
}
```

**Response:**
```json
{
  "response": "Based on the API development guide, here are the FastAPI best practices:\n\n1. **Type Hints**: Use type hints for all function parameters to improve code clarity and enable automatic validation.\n\n2. **Error Handling**: Implement proper error handling to provide meaningful error messages to API consumers.\n\n3. **Documentation**: Add comprehensive documentation to help developers understand and use your API effectively.\n\nThese practices help create robust, maintainable, and user-friendly APIs.\n\nSources used: api-guide.md",
  "sources": ["api-guide.md"]
}
```

### List Available Files

**Endpoint:** `GET /files`

**Response:**
```json
{
  "available_files": ["api-guide.md", "deployment.md"],
  "count": 2,
  "knowledge_directory": "./knowledge"
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "knowledge_files_count": 2,
  "crew_initialized": true
}
```

## Testing Examples

### Using justfile commands (Recommended)

```bash
# Run comprehensive tests
just test

# Interactive testing mode
just test-interactive

# Quick health check
just health

# List available files
just files

# Test a specific query
just query "What are the FastAPI best practices for API development?"
```

### Using curl directly

```bash
# Test query
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "How should I handle authentication in FastAPI?"}'

# List files  
curl "http://localhost:8000/files"

# Health check
curl "http://localhost:8000/health"
```

### Using Python requests

```python
import requests

# Query the knowledge base
response = requests.post(
    "http://localhost:8000/query",
    json={"query": "What are the deployment best practices?"}
)
result = response.json()
print(f"Response: {result['response']}")
print(f"Sources: {result['sources']}")
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes | - |
| `KNOWLEDGE_DIR` | Directory containing markdown files | No | `./knowledge` |

### Knowledge Configuration

The application uses these CrewAI Knowledge settings:
- **Results Limit**: 5 (top 5 relevant chunks returned)
- **Score Threshold**: 0.3 (minimum relevance score)
- **LLM Model**: gpt-4o-mini (fast and efficient)
- **Temperature**: 0.1 (focused, consistent responses)

## Architecture

### Components

1. **KnowledgeManager**: Handles CrewAI knowledge source setup and crew initialization
2. **FastAPI App**: Provides REST API endpoints
3. **CrewAI Agent**: Knowledge synthesizer agent optimized for document retrieval
4. **Static Task**: Pre-defined task with input templating using `{query}` placeholder
5. **Knowledge Sources**: TextFileKnowledgeSource instances for each markdown file

### Task Implementation

The application uses CrewAI's input templating feature:
- **Static Task Definition**: Task created once with `{query}` placeholder in description
- **Input Templating**: Variables passed via `crew.kickoff(inputs={"query": user_query})`
- **Reusable Crew**: Same task instance handles all queries with different inputs

### Source Attribution Strategy

The application attempts source attribution through multiple methods:
1. **Prompt Engineering**: Agent instructed to mention source files in responses
2. **Response Parsing**: Extracts mentioned filenames from agent responses  
3. **Fallback Detection**: Identifies files mentioned anywhere in the response
4. **Metadata Tracking**: Uses CrewAI knowledge source metadata when available

## Limitations & Notes

- **Manual Reload**: Restart the application to refresh knowledge files
- **Source Attribution**: Limited by CrewAI's current knowledge retrieval capabilities
- **File Types**: Currently supports only `.md` files (can be extended to other text formats)
- **LLM Dependency**: Requires external LLM API (OpenAI by default)

## Troubleshooting

### Common Issues

1. **"No .md files found"**: Ensure markdown files are in the `./knowledge/` directory
2. **"Crew not initialized"**: Check if OpenAI API key is set correctly  
3. **"Knowledge source errors"**: Verify file permissions and valid markdown syntax
4. **"API key error"**: Confirm OPENAI_API_KEY environment variable is set

### Debug Mode

Enable verbose logging by setting the log level:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Development

### Running Tests

```bash
just test
# or for interactive mode:
just test-interactive
```

### Code Formatting & Linting

```bash
# Format code with ruff
just format

# Lint code
just lint

# Lint and auto-fix issues
just lint-fix

# Run all quality checks
just check
```

### Adding New Knowledge Sources

To add support for other file types:

1. Import the appropriate CrewAI knowledge source
2. Modify `_setup_knowledge()` method in `KnowledgeManager`
3. Update file discovery logic

Example for PDF support:
```python
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# In _setup_knowledge method:
pdf_files = list(self.knowledge_dir.glob("*.pdf"))
for pdf_file in pdf_files:
    knowledge_source = PDFKnowledgeSource(
        file_paths=[pdf_file.name]
    )
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks: `just check`
5. Test your changes: `just test`
6. Submit a pull request

## Quick Start Summary

```bash
# 1. Clone the repository
git clone <repository-url>
cd fastapi-crewai-poc

# 2. Setup project (checks requirements, installs dependencies)
just setup

# 3. Configure environment
just init-env
# Edit .env with your OpenAI API key

# 4. Start development server
just dev

# 5. Test the API
just test
```

## License

MIT License - feel free to use this code for your projects!

---

**Success Criteria Met:**
✅ User can place markdown files in knowledge folder  
✅ Start the app with simple command  
✅ Query knowledge via API  
✅ Receive responses with source attribution  
✅ Built with latest FastAPI and CrewAI  
✅ Uses uv for project management