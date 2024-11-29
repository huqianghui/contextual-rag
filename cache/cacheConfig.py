from diskcache import Cache
import os
import functools
import hashlib
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
cache = Cache(os.getenv("CACHE_DIR_PATH","cache") + "/azureOpenAICache")

def async_diskcache(cacheName):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a unique cache key
            cache_key = _key_function(cacheName,*args)
            if cache_key in cache:
                logging.info(f"Cache hit for {cacheName} with key {cache_key}")
                return cache[cache_key]
            else:
                logging.info(f"Cache miss for {cacheName} with key {cache_key}")
                try:
                    # Await the async function
                    result = await func(*args, **kwargs)
                except Exception as e:
                    # Do not cache the result, re-raise the exception
                    raise
                else:
                    # Store the result in the cache
                    logging.info(f"Storing result in cache for {cacheName} with key {cache_key}")
                    cache[cache_key] = result
                    return result
        return wrapper
    return decorator

def _key_function(cacheName:str,useCode:str,answer:str,index:int):
    combined_str = cacheName +  useCode + answer
    hash_object = hashlib.sha256(combined_str.encode())
    return hash_object.hexdigest()