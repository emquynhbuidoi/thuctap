import asyncio
from duckduckgo_search import AsyncDDGS

async def asearch(word, max_results: int = 2):
    async with AsyncDDGS() as ddgs:
        return await ddgs.atext(word, max_results=max_results)

async def get_asearch(prompts: str, max_results : int = 2):
    prompts = [w.strip() for w in prompts.split(",")] 
    tasks = [asearch(w, max_results) for w in prompts]
    results = await asyncio.gather(*tasks)
    return [item['body'] for result in results for item in result]
    # return {"results": dict(zip(prompts, results))} 