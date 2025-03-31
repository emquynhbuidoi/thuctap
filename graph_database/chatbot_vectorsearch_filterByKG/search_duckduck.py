import asyncio
from duckduckgo_search import AsyncDDGS

async def asearch(word, max_results: int = 2):
    async with AsyncDDGS() as ddgs:
        return await ddgs.atext(word, max_results=max_results)

async def get_asearch(prompts: str):
    prompts = [w.strip() for w in prompts.split(",")] 
    tasks = [asearch(w, 2) for w in prompts]
    results = await asyncio.gather(*tasks)
    items = [item['body'] for result in results for item in result]
    return "\n".join(items)
    # return {"results": dict(zip(prompts, results))} 