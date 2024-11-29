import asyncio
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

async def process_file(markdownContent,mergedChunkFile):
    async with sem:
        async with aiofiles.open(mergedChunkFile, mode='r') as f:
            mergedChunkFileContent = await f.read()
        fileName = os.path.basename(mergedChunkFile)
        situateContent = await situate_context(markdownContent, mergedChunkFileContent, fileName)
        titelContent = await entitle_chunk(markdownContent, mergedChunkFileContent, fileName)
        return ChunkFinalResult(title=titelContent, chunk=mergedChunkFileContent, context=situateContent, fileName=fileName)

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
  result = await processMergdeChunkFile(mergedChunkFileList)

  # step 3) build the context for each chunk file
  mergedChunkFileList = await get_LLM_chunk_file_list()
  chunkFinalResultList = []
  
  # for mergedChunkFile in mergedChunkFileList:
  #    chunkFinalResult = await process_file(markdownContent,mergedChunkFile)
  #    if chunkFinalResult:
  #      chunkFinalResultList.append(chunkFinalResult)
  #    else:
  #       logging.error(f"process_file error: {mergedChunkFile}")
     

  tasks = [process_file(markdownContent,mergedChunkFile) for mergedChunkFile in mergedChunkFileList]
  results = await asyncio.gather(*tasks)
  chunkFinalResultList.extend(results)

  # step 4) build the AI search index and upload the data to the search index
  # Query rewriting is currently available in the North Europe, and Southeast Asia regions.
  # https://learn.microsoft.com/en-us/azure/search/semantic-how-to-query-rewrite
  # api-version=2024-11-01-preview
  await uploadChunkFinalResult(chunkFinalResultList)



if __name__ == "__main__":
  #clear_cache_by_cache_name("suitate_context")
  #clear_cache_by_cache_name("entitle_chunk")
  reulst = asyncio.run(processPDF("/Users/huqianghui/Downloads/1.git_temp/contextual-rag/testPdf/oral_cancer.pdf"))
