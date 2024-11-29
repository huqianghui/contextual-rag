import logging
import os

from openai import RateLimitError
from promptflow.tracing import start_trace, trace
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from cache.cacheConfig import async_diskcache, cache
from prompt.senamicChunkPrompt import (
    CHUNK_CONTEXT_PROMPT,
    CHUNK_TITLE_PROMPT,
    DOCUMENT_CONTEXT_PROMPT,
)
from roundRobin.azureOpenAIClientRoundRobin import (
    client_manager as asyncAzureOpenAIPromptCacheClientManager,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@async_diskcache("suitate_context")
@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3),retry=retry_if_exception_type(RateLimitError))
async def situate_context(doc: str, chunk: str,chunkName:str) -> str:
    aAzureOpenclient = await asyncAzureOpenAIPromptCacheClientManager.get_next_client()
    try:
        response = await aAzureOpenclient.chat.completions.create(
            model=(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME","gpt-4o-0806")), # the prompr cache support model and api versio Official support for prompt caching was first added in API version 2024-10-01-preview.
            temperature=0.0,
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                            "cache_control": {"type": "ephemeral"} #we will make use of prompt caching for the full documents
                        },
                        {
                            "type": "text",
                            "text": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk),
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"API request failed for chunk {chunkName}: {e}. Retrying...")
        raise e

@async_diskcache("entitle_chunk")
@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3),retry=retry_if_exception_type(RateLimitError))
async def entitle_chunk(doc: str, chunk: str,chunkName:str) -> str:
    aAzureOpenclient = await asyncAzureOpenAIPromptCacheClientManager.get_next_client()
    try:
        response = await aAzureOpenclient.chat.completions.create(
            model=(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME","gpt-4o-0806")), # the prompr cache support model and  Official support for prompt caching was first added in API version 2024-10-01-preview.
            temperature=0.0,
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                            "cache_control": {"type": "ephemeral"} #we will make use of prompt caching for the full documents
                        },
                        {
                            "type": "text",
                            "text": CHUNK_TITLE_PROMPT.format(chunk_content=chunk),
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"API request failed for chunk {chunkName}: {e}. Retrying...")
        raise e


