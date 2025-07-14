# FastAPI + CrewAI Knowledge PoC - Project Commands
# Requires: just (https://just.systems/)

# Default recipe to display help
_default:
    @just --list --unsorted

# Install dependencies using uv
install:
    @echo "📦 Installing dependencies..."
    uv sync

# Install development dependencies
install-dev:
    @echo "📦 Installing development dependencies..."
    uv sync --dev

# Set up the project for development
setup:
    @echo "🚀 Setting up FastAPI + CrewAI Knowledge PoC"
    @echo "=" * 50
    @just check-requirements
    @just install
    @just check-env
    @echo ""
    @echo "✅ Setup complete!"
    @echo ""
    @echo "📋 Next steps:"
    @echo "1. Edit .env and add your OpenAI API key"
    @echo "2. Start the server: just dev"
    @echo "3. Test the API: just test"
    @echo ""
    @echo "🌐 Once running, visit:"
    @echo "   - API docs: http://localhost:8000/docs"
    @echo "   - Health check: http://localhost:8000/health"

# Check if required tools are available
check-requirements:
    @echo "🔍 Checking requirements..."
    @python3 --version || (echo "❌ Python 3.11+ required" && exit 1)
    @uv --version || (echo "❌ uv package manager required. Install from: https://docs.astral.sh/uv/" && exit 1)
    @echo "✅ All requirements met"

# Check environment setup
check-env:
    @echo "🔧 Checking environment setup..."
    @if [ ! -f .env ]; then \
        echo "⚠️  .env file not found. Creating one based on .env.template..."; \
        cp .env.template .env; \
        echo "✅ .env created. Please edit it and add your OpenAI API key."; \
    fi
    @if [ ! -d knowledge ]; then \
        echo "📁 Creating knowledge directory..."; \
        mkdir -p knowledge; \
    fi
    @if [ -z "$(ls -A knowledge 2>/dev/null)" ]; then \
        echo "⚠️  knowledge/ directory is empty. Add some .md files to test the system."; \
    else \
        echo "✅ Knowledge files found: $(ls knowledge/*.md 2>/dev/null | wc -l | tr -d ' ') files"; \
    fi

# Start the FastAPI development server
dev:
    @echo "🚀 Starting FastAPI development server..."
    @echo "Available endpoints:"
    @echo "  POST http://localhost:8000/query - Submit queries"
    @echo "  GET  http://localhost:8000/files - List knowledge files"
    @echo "  GET  http://localhost:8000/health - Health check"
    @echo "  GET  http://localhost:8000/docs - API documentation"
    @echo ""
    uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start the server in production mode
start:
    @echo "🚀 Starting FastAPI server (production mode)..."
    uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Run comprehensive API tests
test:
    @echo "🧪 Running API tests..."
    uv run python test_api.py

# Run interactive testing mode
test-interactive:
    @echo "🤖 Starting interactive testing mode..."
    uv run python test_api.py --interactive

# Format code with ruff
format:
    @echo "🎨 Formatting code with ruff..."
    uv run ruff format .

# Lint code with ruff
lint:
    @echo "🔍 Linting code with ruff..."
    uv run ruff check .

# Lint and fix code issues
lint-fix:
    @echo "🔧 Linting and fixing code with ruff..."
    uv run ruff check --fix .

# Run all quality checks
check: lint format
    @echo "✅ All quality checks completed"

# Clean up temporary files and caches
clean:
    @echo "🧹 Cleaning up temporary files..."
    @find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @find . -type f -name "*.pyc" -delete 2>/dev/null || true
    @find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    @rm -rf .ruff_cache/ 2>/dev/null || true
    @rm -rf build/ dist/ 2>/dev/null || true
    @echo "   Cleaned Python cache files"

# Check API health
health:
    @echo "🏥 Checking API health..."
    @curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API not responding. Is the server running?"

# List available knowledge files
files:
    @echo "📚 Available knowledge files:"
    @curl -s http://localhost:8000/files | python -m json.tool || echo "❌ API not responding. Is the server running?"

# Quick query example
query QUESTION="What are FastAPI best practices?":
    @echo "❓ Querying: {{QUESTION}}"
    @curl -s -X POST http://localhost:8000/query \
        -H "Content-Type: application/json" \
        -d '{"query": "{{QUESTION}}"}' | python -m json.tool || echo "❌ API not responding. Is the server running?"
