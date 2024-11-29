import base64
import json
import os
from dataclasses import dataclass

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    ContentFormat,
    DocumentAnalysisFeature,
)
from azure.ai.formrecognizer import AnalysisFeature
from azure.ai.formrecognizer import AnalyzeResult as FormRecognizerAnalyzeResult
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential

from cache.cacheConfig import async_diskcache, cache

load_dotenv()

USE_DOC_INTEL_PREVIEW_VERSION = True
DOC_INTEL_MODEL_ID = "prebuilt-layout" # E.g. "prebuilt-read", "prebuilt-layout", or "prebuilt-document"

# Possible Document Intelligence features
# v4.0 (Preview): ['ocrHighResolution', 'languages', 'barcodes', 'formulas', 'styleFont', 'keyValuePairs', 'queryFields']
# v3.3 (GA):      ['ocrHighResolution', 'languages', 'barcodes', 'formulas', 'styleFont']
DOC_INTEL_FEATURES = ['ocrHighResolution', 'languages', 'styleFont']
# Load environment variables from Function App local settings file
DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
DOC_INTEL_API_KEY = os.getenv("DOC_INTEL_API_KEY")

asycDocumentIntelligenceClient = DocumentIntelligenceClient(
        endpoint=DOC_INTEL_ENDPOINT, 
        credential=AzureKeyCredential(DOC_INTEL_API_KEY),
        api_version="2024-07-31-preview",
    )
enabled_features = [DocumentAnalysisFeature(feature) for feature in DOC_INTEL_FEATURES]


async def convert_pdf_to_base64(pdf_path: str):
    # Read the PDF file in binary mode, encode it to base64, and decode to string
    with open(pdf_path, "rb") as file:
        base64_encoded_pdf = base64.b64encode(file.read()).decode()
    return base64_encoded_pdf

@async_diskcache("document_markdown_cache")
@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3))
async def get_document_analysis(pdf_path: str):
    analyze_request = AnalyzeDocumentRequest(bytes_source= await convert_pdf_to_base64(pdf_path))
    poller = await asycDocumentIntelligenceClient.begin_analyze_document(
            model_id=DOC_INTEL_MODEL_ID,
            analyze_request=analyze_request,
            output_content_format=ContentFormat.MARKDOWN,
            features=enabled_features
        )
    analyzedDocumentResult =  await poller.result()

    return analyzedDocumentResult.content


