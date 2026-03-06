"""
Main application entry point for Fantasy Chatbot Layer.
Sets up FastAPI server with chat endpoints.
"""

import asyncio
import logging
import yaml
from concurrent.futures import ThreadPoolExecutor
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
from services.image_search import WikipediaImageSearch

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

# Create LLM runner first (needed by UniverseContext)
llm_runner = LLMRunner(
    api_url=llm_config['api_url'],
    model=llm_config['model'],
    temperature=llm_config['temperature'],
    max_tokens=llm_config['max_tokens'],
    system_prompt=llm_config['system_prompt']
)

# Create UniverseContext with the LLM runner
universe_context = UniverseContext(universes=universes, llm_runner=llm_runner)

# Create a separate LLM runner for topic validation with a different system prompt
topic_validator_llm = LLMRunner(
    api_url=llm_config['api_url'],
    model=llm_config['model'],
    temperature=0.1,  # Lower temperature for more consistent validation
    max_tokens=200,  # Short responses for validation
    system_prompt=validation_config.get('topic_validation_prompt', '')
)

# Create topic validator using the validation LLM
topic_validator = TopicValidator(
    universes=universes,
    llm_runner=topic_validator_llm
)

# Create image searcher and shared thread pool executor
image_searcher = WikipediaImageSearch()
_executor = ThreadPoolExecutor(max_workers=4)

# Path for saving proxied images
IMAGE_SAVE_DIR = Path(__file__).parent / "web_interface" / "images"


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
    children_mode: bool = False


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


def clean_llm_response(response: str) -> str:
    """
    Clean LLM response by removing analysis steps and formatting.

    Args:
        response: Raw LLM response

    Returns:
        Cleaned response with just the answer
    """
    import re

    # Remove markdown headers (##, ###, etc.)
    response = re.sub(r'^#+\s+', '', response, flags=re.MULTILINE)

    # Remove bold markers (**text**)
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)

    # Remove italic markers (*text*)
    response = re.sub(r'\*(.*?)\*', r'\1', response)

    # Remove bullet points and numbered lists
    response = re.sub(r'^[\*\-\d]+\.\s+', '', response, flags=re.MULTILINE)

    # Remove "Analyze the Request" section (more robust pattern)
    response = re.sub(r'Analyze the Request:.*?(?=Identify Key Information Needed:|Identify Key Information:|Identify Key:|$)', '', response, flags=re.DOTALL)

    # Remove "Identify Key Information" section (more robust pattern)
    response = re.sub(r'Identify Key Information Needed:.*?(?=Structure the answer:|Structure the answer:|Structure the answer:|$)', '', response, flags=re.DOTALL)

    # Remove "Identify Key Information" section (alternative pattern)
    response = re.sub(r'Identify Key Information:.*?(?=Structure the answer:|Structure the answer:|Structure the answer:|$)', '', response, flags=re.DOTALL)

    # Remove "Identify Key" section (alternative pattern)
    response = re.sub(r'Identify Key:.*?(?=Structure the answer:|Structure the answer:|Structure the answer:|$)', '', response, flags=re.DOTALL)

    # Remove "Structure the answer" section (more robust pattern)
    response = re.sub(r'Structure the answer:.*?(?=Drafting the content:|Drafting the content:|Drafting the content:|$)', '', response, flags=re.DOTALL)

    # Remove "Drafting the content" section (more robust pattern)
    response = re.sub(r'Drafting the content:.*?(?=Answer:|Answer:|Answer:|$)', '', response, flags=re.DOTALL)

    # Remove "Drafting the content" section (alternative pattern)
    response = re.sub(r'Drafting the content.*?(?=Answer:|Answer:|Answer:|$)', '', response, flags=re.DOTALL)

    # Remove "Answer:" prefix if present
    response = re.sub(r'^Answer:\s*', '', response, flags=re.MULTILINE)

    # Remove extra whitespace and newlines
    response = re.sub(r'\n\s*\n+', '\n\n', response)
    response = response.strip()

    return response


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
            reason=f"Invalid universe: {request.universe}",
            conversation_id=request.conversation_id
        )

    # Initialize conversation if needed
    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = []
        
    history = conversations[request.conversation_id]

    # Validate user message against universe
    is_on_topic, reason, extracted_entity = universe_context.validate_query_against_universe(request.message, history)

    if not is_on_topic:
        return ChatResponse(
            response=f"Sorry, I dont think that question is about {request.universe}.",
            is_on_topic=False,
            reason=reason,
            conversation_id=request.conversation_id
        )

    # Rewrite query to include universe context
    rewritten_query = universe_context.rewrite_query(request.message)

    # If children's book mode is enabled, instruct the LLM to simplify language
    if request.children_mode:
        rewritten_query += " This is a story for a child, so use simple words and short to medium length sentences."

    # Get wiki URL for the current universe (before entering the async block)
    current_universe = universe_context.get_current_universe()
    wiki_api_base = current_universe.wiki_api_base if current_universe else None

    # -------------------------------------------------------------------
    # Parallel execution: start LLM text generation and image search at
    # the same time so the user doesn't wait for both sequentially.
    # -------------------------------------------------------------------
    try:
        loop = asyncio.get_event_loop()

        # Wrap both blocking calls so they can run concurrently
        async def run_llm():
            return await loop.run_in_executor(
                _executor,
                lambda: llm_runner.generate_response(
                    user_message=rewritten_query,
                    conversation_history=conversations[request.conversation_id]
                )
            )

        async def run_image_search():
            if not extracted_entity:
                return None
            logger.info(f"Searching image for '{extracted_entity}' on {wiki_api_base or 'Wikipedia'}")
            
            # Step 1: Get the remote URL
            remote_url = await loop.run_in_executor(
                _executor,
                lambda: image_searcher.get_image_url(extracted_entity, request.universe, wiki_api_base)
            )
            
            if not remote_url:
                return None
                
            # Step 2: Download locally to bypass hotlink protection
            local_filename = await loop.run_in_executor(
                _executor,
                lambda: image_searcher.download_image(remote_url, str(IMAGE_SAVE_DIR))
            )
            
            return local_filename

        # Fire both off at the same time
        llm_response, image_filename = await asyncio.gather(run_llm(), run_image_search())

        # Clean the response to remove analysis steps and formatting
        cleaned_response = clean_llm_response(llm_response.content)

        # Validate LLM response
        is_response_valid, response_reason = topic_validator.validate_response(
            cleaned_response,
            rewritten_query
        )

        if not is_response_valid:
            return ChatResponse(
                response=f"I apologize, but I need to stay on topic. {response_reason}",
                is_on_topic=False,
                reason=response_reason,
                conversation_id=request.conversation_id
            )

        final_answer = cleaned_response
        if image_filename:
            image_path = f"/static/images/{image_filename}"
            logger.info(f"Embedding local image: {image_path}")
            final_answer = f"""
<div class="entity-illustration-container">
    <img src="{image_path}" alt="Illustration of {extracted_entity}" class="entity-illustration">
    <div class="entity-caption">{extracted_entity}</div>
</div>
{final_answer}
"""

        # Update conversation history with cleaned response
        conversations[request.conversation_id].append(
            {"role": "user", "content": request.message}
        )
        conversations[request.conversation_id].append(
            {"role": "assistant", "content": cleaned_response} # Store raw content without HTML in history
        )

        # Keep conversation history manageable
        if len(conversations[request.conversation_id]) > 20:
            conversations[request.conversation_id] = conversations[request.conversation_id][-10:]

        return ChatResponse(
            response=final_answer,
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