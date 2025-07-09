# Skill Diff

A tool to help software developers understand what skills they need to move into AI/ML engineering roles by analyzing real job descriptions and comparing them against the user's current skill set.

## Northstar Use Case

"I'm a Java backend developer with 3 years' experience – show me what skills I need to qualify for AI engineering roles."

## Target Users

- **Primary**: Mid-level software developers (3–8 years of experience)
- **Secondary**: Career coaches, tech recruiters, hiring managers

## Technical Architecture

- **Agent Orchestration**: LangGraph for workflow management
- **Job Queue & Caching**: Redis for async processing and caching
- **Database**: PostgreSQL via Supabase with pgvector for vector search
- **API Framework**: FastAPI with built-in metrics endpoint
- **Embedding Model**: OpenAI text-embedding-3-small
- **LLM Backbone**: GPT-4-turbo for classification, extraction, and analysis
- **RAG Pipeline**: For contextual understanding of job descriptions
- **Evaluation Framework**: Custom logic + LLMs to score skill relevance
- **Skills Taxonomy**: Manually curated base layer, augmented with LLMs for normalization

## Development Setup

### Prerequisites

- Python 3.x
- Git

### Quick Start

1. **Set up development environment**:
   ```bash
   make venv
   ```

2. **Install dependencies**:
   ```bash
   make install-dev
   ```

3. **Run all checks**:
   ```bash
   make check
   ```

## Available Commands

### Setup & Dependencies
- `make venv` - Create virtual environment and install dev dependencies
- `make lock` - Lock production and development dependencies
- `make install` - Sync production dependencies and install the project
- `make install-dev` - Sync development dependencies and install the project

### Quality & Testing
- `make test` - Run tests with pytest
- `make lint` - Check for linting errors with Ruff
- `make format` - Format code with Ruff
- `make typecheck` - Run static type checking with Mypy
- `make check` - Run all checks (format check, lint, typecheck, test)

### Build & Clean
- `make clean` - Remove all build artifacts and cache files
- `make build` - Build the package
- `make all` - Set up venv, format code, and run all checks

### Help
- `make help` - Display all available commands

## System Architecture

The system follows a multi-agent architecture using LangGraph to orchestrate different components:

1. **Job Description Analysis**: Extracts skills and requirements from job postings
2. **Skill Matching**: Compares user skills against job requirements using vector search
3. **Gap Analysis**: Identifies missing skills and learning paths
4. **Recommendation Engine**: Suggests specific skills to develop based on career goals

The RAG pipeline enables contextual understanding of job descriptions, while the skills taxonomy provides normalization for variant skill phrasings.
