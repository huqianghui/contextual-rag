import asyncio
import os
import shutil

import aiofiles
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential

from cache.cacheConfig import async_diskcache, cache
from dataClass.dataMode import ChunkResult
from prompt.senamicChunkPrompt import senamicChunkSystemTemplate
from roundRobin.azureOpenAIClientRoundRobin import (
    client_manager as asyncAzureOpenAIStructedOutputClientManager,
)

SEM = asyncio.Semaphore(int(os.getenv("CONCURRENT_SIZE","10")))  # controls the number of concurrent 

async def read_file(file_path):
    """read file content"""
    async with aiofiles.open(file_path, mode='r') as f:
        return await f.read()
    
@async_diskcache("content_chunk_by_llm")
@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3))
async def content_chunk_by_llm(content:str)->list[str]:
    asyncAzureOpenAIClient =  await asyncAzureOpenAIStructedOutputClientManager.get_next_client()
    completion = await asyncAzureOpenAIClient.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_STRUCTURE_OUTPUT_DEPLOYMENT_NAME","gpt-4o-0806"), # replace with the model deployment name of your gpt-4o 2024-08-06 deployment
    messages=[
        {"role": "system", "content": senamicChunkSystemTemplate},
        {"role": "user", "content": content},
    ],
    response_format=ChunkResult)

    chunkResult = completion.choices[0].message.parsed
    return chunkResult

async def parse_file_path(file_path):
    """parse the file path"""
    path, file_name = os.path.split(file_path)
    name, ext = os.path.splitext(file_name)
    return path, name, ext


LLM_CHUNK_PATH = os.getenv("LLM_CHUNK_PATH","./llmChunk/") 
if not os.path.exists(LLM_CHUNK_PATH):
    os.makedirs(LLM_CHUNK_PATH)


async def process_big_chunk_file(file_path):
    """process the file"""
    async with SEM:  # semaphore to control the number of concurrent requests
        # read file content
        file_content = await read_file(file_path)
        # chunk the content by llm
        chunkResult = await content_chunk_by_llm(file_content)
        if chunkResult:
            path, name, ext = await parse_file_path(file_path)
            for index,chunk in enumerate(chunkResult.chunks):
                new_file_name = f"{name}_part_{index}{ext}"
                new_file_path = os.path.join(LLM_CHUNK_PATH, new_file_name)
                async with aiofiles.open(new_file_path, mode='w') as f:
                    await f.write(str(chunk))  # write the chunk to the new file
                    print(f"Saved file: {new_file_path}")
    return {"...processed file_path": file_path}

async def process_small_chunk_file(filepath):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Source file does not exist: {filepath}")

    os.makedirs(LLM_CHUNK_PATH, exist_ok=True)
    dest_file_path = os.path.join(LLM_CHUNK_PATH, os.path.basename(filepath))
    shutil.copy(filepath, dest_file_path)
    print(f"File copied to: {dest_file_path}")

async def get_LLM_chunk_file_list():
    """get the list of LLM chunk files"""
    file_names = os.listdir(LLM_CHUNK_PATH)
    full_paths = [os.path.join(LLM_CHUNK_PATH, file) for file in file_names]
    return full_paths