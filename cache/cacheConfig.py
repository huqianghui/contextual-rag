import functools
import hashlib
import logging
import os

from diskcache import Cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
cache = Cache(os.getenv("CACHE_DIR_PATH","cache") + "/azureOpenAICache")

def async_diskcache(cacheName):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a unique cache key
            cache_key = cacheName + "__" + _key_function(cacheName,*args,**kwargs)
            
            # If the function is called without arguments, do not cache the result
            if(len(args) == 0 and len(kwargs) == 0):
                cache_key = cacheName
                return await func(*args, **kwargs)

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

def _key_function(cacheName:str,*args,**kwargs):
    args_str = ''.join(str(arg) for arg in args)
    kwargs_str = ''.join(f'{k}{str(v)}' for k, v in sorted(kwargs.items()))
    combined_str = cacheName + args_str + kwargs_str
    hash_object = hashlib.sha256(combined_str.encode())
    return hash_object.hexdigest()

def clear_cache_by_cache_name(cacheName:str):
    keys_to_delete = [key for key in cache.iterkeys() if key.startswith(cacheName)]
    for key in keys_to_delete:
        del cache[key]

