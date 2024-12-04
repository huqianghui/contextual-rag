import asyncio
import json
import logging
import os

import aiofiles
import pandas as pd
import tiktoken
from dotenv import load_dotenv
from promptflow.tracing import start_trace, trace
from tenacity import retry, stop_after_attempt, wait_random_exponential

from aiSearch.azureAISearchData import uploadChunkFinalResult
from cache.cacheConfig import async_diskcache, cache, clear_cache_by_cache_name
from contextualProcess.chunkContextual import entitle_chunk, situate_context
from dataClass.dataMode import ChunkFinalResult
from docProces.contentSplit import (
    mergeSpippentsIntoChunk,
    processMergdeChunkFile,
    saveMergedChunkIntoFile,
    splitContentByMarkdownHeader,
)
from docProces.documentReader import get_document_analysis
from docProces.senamicChunk import get_LLM_chunk_file_list

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

sem = asyncio.Semaphore(2)  # controls the number of concurrent requests

# set the path to save the final chunk file
FINAL_CHUNK_FILE_PATH = os.getenv("FINAL_CHUNK_FILE_PATH","./finalChunk/")
if not os.path.exists(FINAL_CHUNK_FILE_PATH):
    os.makedirs(FINAL_CHUNK_FILE_PATH)

async def contextual_process_file(markdownContent,mergedChunkFile):
    async with sem:
        async with aiofiles.open(mergedChunkFile, mode='r') as f:
            mergedChunkFileContent = await f.read()
        fileName = os.path.basename(mergedChunkFile)
        situateContent = await situate_context(markdownContent, mergedChunkFileContent, fileName)
        titelContent = await entitle_chunk(markdownContent, mergedChunkFileContent, fileName)
        chunk_result = ChunkFinalResult(title=titelContent, chunk=mergedChunkFileContent, context=situateContent, fileName=fileName)

        output_file = f"{fileName}_finalchunk.json"
        async with aiofiles.open(FINAL_CHUNK_FILE_PATH + output_file, 'w',encoding="utf-8") as json_file:
            await json_file.write(json.dumps(chunk_result.__dict__, ensure_ascii=False))

        return chunk_result

async def processPDF(pdf_path:str):

  fileName = os.path.basename(pdf_path)
  # step 1) read the pdf by Azure Document intelligence and get the markdown 
  markdownContent = await get_document_analysis(pdf_path)
  encoding = tiktoken.get_encoding("o200k_base")
  totalTokenCount = len(encoding.encode(markdownContent))
  logging.info(f"***entire pdf totalTokenCount: {totalTokenCount}")


  # step 2) chunk the markdown content by llm
  splitResult = await splitContentByMarkdownHeader(markdownContent) 
  mergedChunkList =  await mergeSpippentsIntoChunk(splitResult)
  mergedChunkFileList =await saveMergedChunkIntoFile(mergedChunkList)
  await processMergdeChunkFile(mergedChunkFileList)

  # step 3) build the context for each chunk file and save to final chunk files
  llmProcessedChunkFileList = await get_LLM_chunk_file_list()
  chunkFinalResultList = []
  
  # for processedChunkFile in llmProcessedChunkFileList:
  #    chunkFinalResult = await contextual_process_file(markdownContent,processedChunkFile)
  #    if chunkFinalResult:
  #      chunkFinalResultList.append(chunkFinalResult)
  #    else:
  #       logging.error(f"process_file error: {processedChunkFile}")
     
  tasks = [contextual_process_file(markdownContent,processedChunkFile) for processedChunkFile in llmProcessedChunkFileList]
  results = await asyncio.gather(*tasks)
  chunkFinalResultList.extend(results)

  # step 4) build the AI search index and upload the data to the search index
  # Query rewriting is currently available in the North Europe, and Southeast Asia regions.
  # https://learn.microsoft.com/en-us/azure/search/semantic-how-to-query-rewrite
  # api-version=2024-11-01-preview
  await uploadChunkFinalResult(chunkFinalResultList)



if __name__ == "__main__":
  clear_cache_by_cache_name("suitate_context")
  clear_cache_by_cache_name("entitle_chunk")
  reulst = asyncio.run(processPDF("/Users/huqianghui/Downloads/231220_71213901009华思雯_11~13.pdf"))
