import asyncio
import os
import shutil

import tiktoken
from dotenv import load_dotenv
from langchain.text_splitter import MarkdownHeaderTextSplitter

from dataClass.dataMode import MergedChunk, MergedChunkFile, SplitResult
from docProces.senamicChunk import process_big_chunk_file, process_small_chunk_file

load_dotenv()


headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3")
]

text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)


async def splitContentByMarkdownHeader(docMarkdownStr:str)->list[SplitResult]:
    splits = text_splitter.split_text(docMarkdownStr)
    encoding = tiktoken.get_encoding(os.getenv("LLM_CODER","o200k_base"))
    splitResult = []
    for  split in splits:
        split_token_count = len(encoding.encode(split.page_content))
        splitResult.append(SplitResult(tokens=split_token_count,content=split.page_content))
    return splitResult


# set the 
SPIPPETS_SIZE=int(os.getenv("SPIPPETS_SIZE","300"))
# set the miminum size of the split content  
CHUNK_MIN_SIZE = int(os.getenv("CHUNK_MIN_SIZE","800"))  
# set the maximum size of the split content
CHUNK_MAX_SIZE = int(os.getenv("CHUNK_MAX_SIZE","1200"))    


async def mergeSpippentsIntoChunk(splitResult: list[SplitResult]) -> list[MergedChunk]:
    # store the merged chunks  
    mergedChunkList = []  
    index = 0  # current index of the split result
    while index < len(splitResult):
        print("...processing the split: " + str(index))  
        currentSplit = splitResult[index]
        currentSplitContent = currentSplit.content
        currentSplitTokens = currentSplit.tokens

        # if the current split is bigger than the maximum size, keep it as is
        if CHUNK_MIN_SIZE <= currentSplitTokens:  
            mergedChunk = MergedChunk(splits=currentSplitContent, totalTokens=currentSplitTokens, note="it is bigger than chunk min size,keep as is")
            mergedChunkList.append(mergedChunk)  
            index += 1   
        # if the current split is smaller than the minimum size, merge it with the next split
        else:
            combinedTokens = currentSplitTokens  
            combinedContent = currentSplitContent
            index += 1  
    
            while combinedTokens < CHUNK_MAX_SIZE and index < len(splitResult):
                currentSplit = splitResult[index]
                currentSplitContent = currentSplit.content
                currentSplitTokens = currentSplit.tokens 
                combinedTokens += currentSplitTokens

                if combinedTokens < CHUNK_MAX_SIZE or currentSplitTokens < SPIPPETS_SIZE or ((combinedTokens -currentSplitTokens) < SPIPPETS_SIZE) :
                    # if combined tokens is less than the maximum size, add the current split to the combined content or the chunk is less than the spippet size
                    combinedContent += currentSplitContent
                    index += 1
                else:
                    # remove the last split if the combined tokens is greater than the maximum size
                    combinedTokens -=currentSplitTokens
                    break  
                
            mergedChunk = MergedChunk(splits=combinedContent, totalTokens=combinedTokens, note="it is bigger than chunk min size,keep as is")
            mergedChunkList.append(mergedChunk)
    return mergedChunkList


# set the path to save the merged chunk file
MERGE_CHUNK_FILE_PATH = os.getenv("MERGE_CHUNK_FILE_PATH","./mergedChunk/")
if not os.path.exists(MERGE_CHUNK_FILE_PATH):
    os.makedirs(MERGE_CHUNK_FILE_PATH)

async def saveMergedChunkIntoFile(mergedChunkList: list[MergedChunk])->list[MergedChunkFile]:

    MergedChunkFileList = []
    for idx, chunk in enumerate(mergedChunkList):  
        file_name = f"{idx}_chunk_tokens_{chunk.totalTokens}.md"
        abPath = MERGE_CHUNK_FILE_PATH + file_name
        
        mergedChunkFile=MergedChunkFile(filePath=abPath,totalTokens=chunk.totalTokens)
        MergedChunkFileList.append(mergedChunkFile)
        
        with open(abPath, "w", encoding="utf-8") as file:
            file.write(chunk.splits)
    return MergedChunkFileList

async def processMergdeChunkFile(mergedChunkFileList:list[MergedChunkFile]):
    chunkTasks = [process_big_chunk_file(mergedChunkFile.filePath) for mergedChunkFile in mergedChunkFileList if mergedChunkFile.totalTokens >= CHUNK_MAX_SIZE]
    copyTasks = [process_small_chunk_file(mergedChunkFile.filePath) for mergedChunkFile in mergedChunkFileList if mergedChunkFile.totalTokens < CHUNK_MAX_SIZE]
    await asyncio.gather(*copyTasks)
    # run the tasks concurrently
    results = await asyncio.gather(*chunkTasks)
    print(results)





