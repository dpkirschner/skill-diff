Purpose:
A tool to help software developers understand what skills they need to move into AI/ML engineering roles by analyzing real job descriptions and comparing them against the user’s current skill set.

Northstar Use Case:
“I’m a Java backend developer with 3 years’ experience – show me what skills I need to qualify for AI engineering roles.”

Target Users:
	•	Primary: Mid-level software developers (3–8 years of experience)
	•	Secondary: Career coaches, tech recruiters, hiring managers

⸻

🧱 Technical Overview

System Architecture:
	•	Agent Orchestration: LangGraph
	•	Job Queue & Caching: Redis
	•	Database: PostgreSQL via Supabase, using pgvector for vector search
	•	API Framework: FastAPI (includes built-in metrics endpoint)
	•	Embedding Model: OpenAI text-embedding-3-small
	•	LLM Backbone: GPT-4-turbo (used for classification, extraction, and analysis)
	•	RAG Pipeline: For contextual understanding of job descriptions
	•	Evaluation Framework: Custom logic + LLMs to score relevance of skills
	•	Skills Taxonomy: Manually curated base layer, augmented with LLMs to normalize variant phrasing
