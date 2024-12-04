senamicChunkSystemTemplate='''
You are an expert in content chunking. Please help me chunk user's input text according to the following requirements
                    1. Truncate the text content into chunks of no more than 1200 tokens, no less than 800 tokens.
                    2. Make each chunk hold a similar number of tokens as much as possible, keeping it between 800 and 1200 tokens.
                    3. Each chunk part should maintain contextual coherence and preserve the integrity and independence of the semantics as much as possible in one chunk.
                    4. The truncated content should be retained in its entirety without any additions or modifications.
                    5. Each chunked part is output original markdown format 
                    6. If the markdown element is table, keep the entire table and the table's introduction and description in on chunk, even the size more than 1200 tokens. 
                    7. The final output is a markdown string array [ "chunked1markdown" , "chunked2markdown",....]
'''

DOCUMENT_CONTEXT_PROMPT = """
<document>
{doc_content}
</document>
"""


CHUNK_CONTEXT_PROMPT = """
Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

Please give a short succinct context to situate this chunk less then 150 words.  within the overall document for the purposes of improving search retrieval of the chunk.
Answer only with the succinct context and nothing else.
Output the result in chunk content language which means the chunk content is in Chinese, please answer in Chinese. 
"""

CHUNK_TITLE_PROMPT = """
Here is the chunk we want to entitle within the whole document
<chunk>
{chunk_content}
</chunk>

Please give a short entitle to descript and summary this chunk less then 50 words. within the overall document for the purposes of improving search retrieval of the chunk.
Answer only with the title and nothing else.
Output the result in chunk content language which means the chunk content is in Chinese, please answer in Chinese. 
"""