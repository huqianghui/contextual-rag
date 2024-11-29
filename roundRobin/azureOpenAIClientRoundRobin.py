import asyncio
import logging
import os

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv(verbose=True)

api_base1 = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key1= os.getenv("AZURE_OPENAI_API_KEY")
api_base2 = os.getenv("AZURE_OPENAI_ENDPOINT2")
api_key2= os.getenv("AZURE_OPENAI_API_KEY2")
api_base3 = os.getenv("AZURE_OPENAI_ENDPOINT3")
api_key3= os.getenv("AZURE_OPENAI_API_KEY3")
api_base4 = os.getenv("AZURE_OPENAI_ENDPOINT4")
api_key4= os.getenv("AZURE_OPENAI_API_KEY4")

api_base5 = os.getenv("AZURE_OPENAI_ENDPOINT5")
api_key5= os.getenv("AZURE_OPENAI_API_KEY5")
api_base6 = os.getenv("AZURE_OPENAI_ENDPOINT6")
api_key6= os.getenv("AZURE_OPENAI_API_KEY6")
api_base7 = os.getenv("AZURE_OPENAI_ENDPOINT7")
api_key7= os.getenv("AZURE_OPENAI_API_KEY7")

api_version = os.getenv("AZURE_OPENAI_API_VERSION","2024-10-21")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME","gpt-4o")

aAzureOpenclient1 =  AsyncAzureOpenAI(
        azure_endpoint=api_base1,
        api_key=api_key1,  
        api_version=api_version
    )

aAzureOpenclient2 =  AsyncAzureOpenAI(
        api_key=api_key2,  
        api_version=api_version,
        azure_endpoint=api_base2
    )

aAzureOpenclient3 =  AsyncAzureOpenAI(
        api_key=api_key3,  
        api_version=api_version,
        azure_endpoint=api_base3
    )

aAzureOpenclient4 =  AsyncAzureOpenAI(
        api_key=api_key4,  
        api_version=api_version,
        azure_endpoint=api_base4
    )

aAzureOpenclient5 =  AsyncAzureOpenAI(
        api_key=api_key5,  
        api_version=api_version,
        azure_endpoint=api_base5
    )

aAzureOpenclient6 =  AsyncAzureOpenAI(
        api_key=api_key6,  
        api_version=api_version,
        azure_endpoint=api_base6
    )

aAzureOpenclient7 =  AsyncAzureOpenAI(
        api_key=api_key7,  
        api_version=api_version,
        azure_endpoint=api_base7
    )

class AzureOpenAIClientsRoundRobin:
    def __init__(self, *clients):
        self.clients = clients
        self.client_count = len(clients)
        self.index = 0  # init
        self.lock = asyncio.Lock()
    
    async def get_next_client(self):
        async with self.lock: 
            # get client
            client = self.clients[self.index]
            # update index 
            self.index = (self.index + 1) % self.client_count
            return client

# init client
client_manager = AzureOpenAIClientsRoundRobin(
    aAzureOpenclient1, 
    aAzureOpenclient2, 
    aAzureOpenclient3, 
    aAzureOpenclient4,
    aAzureOpenclient5, 
    aAzureOpenclient6, 
    aAzureOpenclient7
)
