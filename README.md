# ContentFlow: A Localized Multi-Agent AI Orchestrator

## What is it?
ContentFlow is an advanced Artificial Intelligence system leveraging Multi-Agent Systems (MAS) and local Large Language Models (LLMs) to autonomously synthesize complex, long-form digital media. Instead of relying on a standard chatbot interface, it deploys a network of specialized AI neural personas that reason, research, and generate highly structured outputs. The entire ecosystem operates offline on local hardware, ensuring absolute data privacy and zero API dependency.

## How it works (The Core Architecture)

### 1. Multi-Agent System (MAS) Architecture (`agents.py`)
Instead of standard zero-shot prompting, the system engineers a network of specialized AI agents. By utilizing advanced prompt engineering and constraint satisfaction, each agent is programmed with a distinct role:
- **Content Strategist**
- **Domain Expert / Scriptwriter**
- **SEO Specialist**
- **Critic Agent**

This enables distributed problem-solving, where each agent applies domain-specific reasoning to a specific phase of the pipeline.

### 2. Algorithmic Task Orchestration (`tasks.py`)
To prevent LLM hallucinations and manage complex cognitive tasks, the system utilizes a directed workflow engine. It enforces strict sequential dependencies—ensuring that data retrieval and structural outlining must be successfully verified by the Strategist agent before semantic text generation is handed off to the Writer agent.

### 3. Local LLM Inference & Proxy Routing (Ollama + LiteLLM)
The core intelligence engine is designed for edge computing and privacy. It utilizes LiteLLM as an API proxy to route complex, multi-agent framework instructions directly to locally hosted, quantized open-weights models (like Llama 3 or Mistral) running via Ollama. This architecture allows the system to process massive context windows and generate 1200+ word outputs with zero cloud computing costs.

### 4. Context Memory & Execution Hub (`main.py`)
The central orchestrator securely initializes the environment and dynamically manages the token context window. It acts as the central nervous system, handling the critical data hand-offs between agents. It ensures the synthesized output from one AI node is seamlessly injected as the input context for the next, compiling the final structured data package.

### 5. System Evaluation & Hallucination Control (The Extra Major Project Layer)
Because local models are prone to context-loss over long generations, the pipeline includes a dedicated **Critic Agent**. This agent utilizes an "LLM-as-a-judge" evaluation metric. It reviews the final 1200-word output against the initial prompt to detect semantic drift, eliminate hallucinations, and ensure grammatical coherence before saving the final file.

## Hardware and Software Requirements

- **Hardware**: Minimum 16GB RAM (Unified or standard). A dedicated GPU (NVIDIA RTX series) or Apple Silicon (M-series) is highly recommended for efficient, low-latency token generation during local Ollama inference.
- **Software**: Python 3.10+, VS Code (`launch.json` configured), Docker (optional, for isolated deployments).
- **Dependencies**: `crewai`, `litellm`, `ollama-python`, `python-dotenv`

## Why it matters in the real world
The AI industry is rapidly shifting from single-prompt cloud models to autonomous, multi-agent workflows. Managing digital media pipelines at scale requires complex reasoning, SEO optimization, and massive text generation. ContentFlow solves this by proving that sophisticated agentic workflows can be executed securely on local hardware. It provides a highly scalable, privacy-first blueprint for enterprises and creators to generate high-value content without exposing proprietary data to third-party cloud APIs.

## Future Scope
The modular architecture allows for future integration of Vision-Language Models (VLMs) into the local Ollama backend, enabling agents to "watch" local video files and generate timestamped descriptions autonomously. Furthermore, direct API webhooks can be added to the execution hub, allowing the system to automatically push the generated content directly to a WordPress CMS or YouTube Studio.
