# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Skill Diff is a tool to help software developers understand what skills they need to move into AI/ML engineering roles by analyzing real job descriptions and comparing them against the user's current skill set.

**Target Users**: Mid-level software developers (3-8 years experience), career coaches, tech recruiters, and hiring managers.

## Technical Architecture

The system is built using the following technologies:

- **Agent Orchestration**: LangGraph for workflow management
- **Job Queue & Caching**: Redis for async processing and caching
- **Database**: PostgreSQL via Supabase with pgvector for vector search
- **API Framework**: FastAPI with built-in metrics endpoint
- **Embedding Model**: OpenAI text-embedding-3-small
- **LLM Backbone**: GPT-4-turbo for classification, extraction, and analysis
- **RAG Pipeline**: For contextual understanding of job descriptions
- **Evaluation Framework**: Custom logic + LLMs to score skill relevance
- **Skills Taxonomy**: Manually curated base layer, augmented with LLMs for normalization

## Development Commands

Since this is a new repository, standard Python/FastAPI development commands will likely include:
- `pip install -r requirements.txt` - Install dependencies
- `uvicorn main:app --reload` - Run development server
- `pytest` - Run tests
- `python -m pytest tests/` - Run specific test directory

## Architecture Notes

The system follows a multi-agent architecture using LangGraph to orchestrate different components:

1. **Job Description Analysis**: Extracts skills and requirements from job postings
2. **Skill Matching**: Compares user skills against job requirements using vector search
3. **Gap Analysis**: Identifies missing skills and learning paths
4. **Recommendation Engine**: Suggests specific skills to develop based on career goals

The RAG pipeline enables contextual understanding of job descriptions, while the skills taxonomy provides normalization for variant skill phrasings.
