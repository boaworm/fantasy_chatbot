"""
Main application entry point for Fantasy Chatbot Layer.
Sets up FastAPI server with chat endpoints.
"""

import logging
import yaml
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.topic_validator import TopicValidator
from services.llm_runner import LLMRunner, LLMResponse
from services.universe_context import UniverseContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path(__file__).parent / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize services
universes = config['universes']
llm_config = config['llm']
server_config = config['server']
validation_config = config['validation']

universe_context = UniverseContext(universes=universes, llm_runner=llm_runner)

topic_validator = TopicValidator(
    topics=[universe['name'] for universe in universes],
    threshold=validation_config['similarity_threshold'],
    use_fuzzy=validation_config['use_fuzzy_matching']
)

llm_runner = LLMRunner(
    api_url=llm_config['api_url'],
    model=llm_config['model'],
    temperature=llm_config['temperature'],
    max_tokens=llm_config['max_tokens'],
    system_prompt=llm_config['system_prompt']
)

# Create a separate LLM runner for topic validation with a different system prompt
topic_validator_llm = LLMRunner(
    api_url=llm_config['api_url'],
    model=llm_config['model'],
    temperature=0.1,  # Lower temperature for more consistent validation
    max_tokens=200,  # Short responses for validation
    system_prompt=validation_config.get('topic_validation_prompt', '')
)

# Create FastAPI app
app = FastAPI(
    title="Fantasy Chatbot Layer",
    description="Chatbot with topic validation and LLM integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
web_dir = Path(__file__).parent / "web_interface"
app.mount("/static", StaticFiles(directory=web_dir), name="static")


class ChatRequest(BaseModel):
    """Model for chat request."""
    message: str
    universe: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Model for chat response."""
    response: str
    is_on_topic: bool
    reason: Optional[str] = None
    conversation_id: Optional[str] = None


class TopicResponse(BaseModel):
    """Model for topic response."""
    topics: List[str]


# In-memory conversation storage
conversations: dict[str, list] = {}


@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Serve the web interface."""
    web_dir = Path(__file__).parent / "web_interface"
    index_file = web_dir / "index.html"

    if index_file.exists():
        return HTMLResponse(content=index_file.read_text())
    else:
        return HTMLResponse(content="<h1>Web interface not found. Please check installation.</h1>")


@app.get("/api/topics", response_model=TopicResponse)
async def get_topics():
    """Get the list of allowed topics."""
    return TopicResponse(topics=[universe['name'] for universe in universes])


@app.get("/api/universes", response_model=TopicResponse)
async def get_universes():
    """Get the list of available universes."""
    return TopicResponse(topics=[universe['name'] for universe in universes])


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message through the chatbot layer.

    1. Set the current universe
    2. Validate user question is related to the universe
    3. Rewrite query to include universe context
    4. Generate LLM response
    5. Validate LLM response is within the universe
    6. Return response to user
    """
    # Set the current universe
    if not universe_context.set_universe(request.universe):
        return ChatResponse(
            response=f"I'm sorry, but I don't have information about '{request.universe}'. Please select a valid universe from the dropdown.",
            is_on_topic=False,
            reason=f"Invalid universe: {request.universe}"
        )

    # Validate user message against universe
    is_on_topic, reason = universe_context.validate_query_against_universe(request.message)

    if not is_on_topic:
        return ChatResponse(
            response=f"I'm sorry, but I can only discuss topics related to {request.universe}. {reason}",
            is_on_topic=False,
            reason=reason
        )

    # Initialize conversation if needed
    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = []

    # Rewrite query to include universe context
    rewritten_query = universe_context.rewrite_query(request.message)

    # Generate LLM response
    try:
        llm_response = llm_runner.generate_response(
            user_message=rewritten_query,
            conversation_history=conversations[request.conversation_id]
        )

        # Validate LLM response
        is_response_valid, response_reason = topic_validator.validate_response(
            llm_response.content,
            rewritten_query
        )

        if not is_response_valid:
            return ChatResponse(
                response=f"I apologize, but I need to stay on topic. {response_reason}",
                is_on_topic=False,
                reason=response_reason
            )

        # Update conversation history
        conversations[request.conversation_id].append(
            {"role": "user", "content": request.message}
        )
        conversations[request.conversation_id].append(
            {"role": "assistant", "content": llm_response.content}
        )

        # Keep conversation history manageable
        if len(conversations[request.conversation_id]) > 20:
            conversations[request.conversation_id] = conversations[request.conversation_id][-10:]

        return ChatResponse(
            response=llm_response.content,
            is_on_topic=True,
            reason="Response is valid and on-topic",
            conversation_id=request.conversation_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing your message: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    llm_healthy = llm_runner.health_check()

    return {
        "status": "healthy" if llm_healthy else "degraded",
        "llm_healthy": llm_healthy,
        "universes_count": len(universes)
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=server_config['host'],
        port=server_config['port'],
        reload=server_config['debug']
    )