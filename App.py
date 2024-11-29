import asyncio
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI
from promptflow.tracing import start_trace, trace
from tenacity import retry, stop_after_attempt, wait_random_exponential

from cache.cacheConfig import async_diskcache, cache
from prompt.senamicChunkPrompt import systemTemplateCodeModify
from roundRobin.azureOpenAIClientRoundRobin import client_manager

ERROR_CODE="ERR_101: \n"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

azureOpenAIClient = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_KEY"),  
  api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

@async_diskcache("judge_code_by_o1_preivew_moddel")
@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3))
async def judge_code_by_o1_preivew_moddel(useCode:str,answer:str,index:int):
    pass
    # user_prompt_code_modify_content = user_prompt_code_modify.format(user_code=useCode, answer=answer)
    # aAzureOpenclient = await client_manager.get_next_client()
    # # "Unsupported value: 'messages[0].role' does not support 'system' with this model.
    # try:
    #     response = await aAzureOpenclient.chat.completions.create(
    #         model=os.getenv("AZURE_OPENAI_O1_DEPLOYMENT_NAME","o1-preview"),
    #         messages=[
    #         {
    #             "role": "user",
    #             "content": systemTemplateCodeModify
    #         },
    #         {
    #             "role": "user",
    #             "content": str(user_prompt_code_modify_content)
    #         }]
    #     )
    #     return response.choices[0].message.content
    # except Exception as e:
    #     logging.error(f"API request failed for row {index + 1}: {e}. Retrying...")
    #     raise e

@async_diskcache("judge_code_by_o1_mini_moddel")
@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3))
async def judge_code_by_o1_mini_moddel(useCode:str,answer:str,index:int):
    pass
    # user_prompt_code_modify_content = user_prompt_code_modify.format(user_code=useCode, answer=answer)
    # aAzureOpenclient = await client_manager.get_next_client()
    # try:
    #     response = await aAzureOpenclient.chat.completions.create(
    #         model=os.getenv("AZURE_OPENAI_O1_MINI_DEPLOYMENT_NAME","o1-mini"),
    #         messages=[
    #         {
    #             "role": "user",
    #             "content": systemTemplateCodeModify
    #         },
    #         {
    #             "role": "user",
    #             "content": str(user_prompt_code_modify_content)
    #         }]
    #     )
    #     return response.choices[0].message.content
    # except Exception as e:
    #     logging.error(f"{ERROR_CODE} >> API request failed for row {index + 1}: {e}. Retrying...")
    #     raise e

if __name__ == "__main__":
   start_trace()

