import asyncio
import os
import re

from azure.search.documents.indexes.models import (
    AzureOpenAIParameters,
    AzureOpenAIVectorizer,
    CorsOptions,
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from dotenv import load_dotenv
from tqdm import tqdm

from aiSearch.azureAISearchClient import get_index_client, get_search_client
from aiSearch.dataModel import Entity
from dataClass.dataMode import ChunkFinalResult
from roundRobin.azureOpenAIClientRoundRobin import (
    client_manager as asyncAzureOpenAIClientManager,
)

load_dotenv()

index_name = os.getenv("AZURE_AI_SERACH_INDEX_NAME")

async def create_search_index(index_name, index_client):
    print(f"Ensuring search index {index_name} exists")
    if index_name not in index_client.list_index_names():
        
        index = SearchIndex(
            name=index_name,
            cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=600),
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True,searchable=True, filterable=True, sortable=True, facetable=True),
                SearchableField(name="fileName",searchable=True, filterable=True, sortable=True, facetable=True,type=SearchFieldDataType.String, analyzer_name="zh-Hans.microsoft"),
                SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="zh-Hans.microsoft"),
                SearchableField(name="context", type=SearchFieldDataType.String, analyzer_name="zh-Hans.microsoft"),
                SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="zh-Hans.microsoft"),
                SearchField(name="title_embedding", 
                            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                            hidden=False, 
                            searchable=True, 
                            filterable=False, 
                            sortable=False, 
                            facetable=False,
                            vector_search_dimensions=1536, 
                            vector_search_profile_name="azureOpenAIHnswProfile"),
                SearchField(name="context_embedding", 
                            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                            hidden=False, 
                            searchable=True, 
                            filterable=False, 
                            sortable=False, 
                            facetable=False,
                            vector_search_dimensions=1536, 
                            vector_search_profile_name="azureOpenAIHnswProfile"),
                SearchField(name="content_embedding", 
                            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                            hidden=False, 
                            searchable=True, 
                            filterable=False, 
                            sortable=False, 
                            facetable=False,
                            vector_search_dimensions=1536, 
                            vector_search_profile_name="azureOpenAIHnswProfile")
            ],
            semantic_search=SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[
                                SemanticField(field_name="content")
                            ],
                            keywords_fields=[
                                SemanticField(field_name="context")
                            ]
                        ),
                    )
                ]
            ),
            vector_search=VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
                profiles=[VectorSearchProfile(name="azureOpenAIHnswProfile",algorithm_configuration_name="myHnsw",vectorizer="azureOpenAIVectorizer")],
                vectorizers=[
                    AzureOpenAIVectorizer(
                        name="azureOpenAIVectorizer",
                        azure_open_ai_parameters=AzureOpenAIParameters(
                            resource_uri=os.getenv("AZURE_OPENAI_ENDPOINT"),
                            deployment_id=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
                            model_name=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
                            api_key=os.getenv("AZURE_OPENAI_API_KEY")))
                ]
            )
        )
        print(f"Creating {index_name} search index")
        index_client.create_index(index)
    else:
        print(f"Search index {index_name} already exists")

async def upload_entities_to_index(entities, upload_batch_size=50):
    
    search_client = get_search_client()

    to_upload_dicts = []

    for entity in entities:
        # add id to documents
        entity_dict = entity.__dict__
        entity_dict.update({"@search.action": "upload", "id": str(entity_dict["id"])})

        if "description_embedding" in entity_dict and entity_dict["description_embedding"] is None:
            del entity_dict["description_embedding"]

        to_upload_dicts.append(entity_dict)

    # Upload the documents in batches of upload_batch_size
    for i in tqdm(
        range(0, len(to_upload_dicts), upload_batch_size), desc="Indexing Chunks..."
    ):
        batch = to_upload_dicts[i : i + upload_batch_size]
        results = search_client.upload_documents(documents=batch)
        num_failures = 0
        errors = set()
        for result in results:
            if not result.succeeded:
                print(
                    f"Indexing Failed for {result.key} with ERROR: {result.error_message}"
                )
                num_failures += 1
                errors.add(result.error_message)
        if num_failures > 0:
            raise Exception(
                f"INDEXING FAILED for {num_failures} documents. Please recreate the index."
                f"To Debug: PLEASE CHECK chunk_size and upload_batch_size. \n Error Messages: {list(errors)}"
            )

semaphore = asyncio.Semaphore(10)

async def process_chunk(chunkFinalResult, index):
     async with semaphore:
        embeddingDeploymentName = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        asyncAzureOpenAIClient  = await asyncAzureOpenAIClientManager.get_next_client()
        id = chunkFinalResult.fileName + "_chunk_" + str(index)
        sanitized_key = re.sub(r"[^a-zA-Z0-9_\-]", "", id)
        titleEmbeddingTask =   asyncio.create_task(asyncAzureOpenAIClient.embeddings.create(input = chunkFinalResult.title,model = embeddingDeploymentName))
        contextEmbeddingTask =   asyncio.create_task(asyncAzureOpenAIClient.embeddings.create(input = chunkFinalResult.context,model = embeddingDeploymentName))
        contentEmbeddingTask =   asyncio.create_task(asyncAzureOpenAIClient.embeddings.create(input = chunkFinalResult.chunk,model = embeddingDeploymentName))
        results = await asyncio.gather(titleEmbeddingTask, contextEmbeddingTask, contentEmbeddingTask)
        titleEmbedding = results[0].data[0].embedding
        contextEmbedding = results[1].data[0].embedding
        contentEmbedding = results[2].data[0].embedding
        entity = Entity(id=sanitized_key,fileName = chunkFinalResult.fileName,title=chunkFinalResult.title,context=chunkFinalResult.context,content=chunkFinalResult.chunk,title_embedding=titleEmbedding,context_embedding=contextEmbedding,content_embedding=contentEmbedding)
        return entity

async def uploadChunkFinalResult(chunkFialResultList: list[ChunkFinalResult]):
    await create_search_index(index_name, get_index_client())
    entities = []
    tasks = []

    for index, chunkFinalResult in enumerate(chunkFialResultList):
        tasks.append( process_chunk(chunkFinalResult, index))

    # Gather all results
    entities = await asyncio.gather(*tasks)
    await upload_entities_to_index(entities)


