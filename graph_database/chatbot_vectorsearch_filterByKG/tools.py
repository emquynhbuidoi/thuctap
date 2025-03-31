import asyncio
from duckduckgo_search import AsyncDDGS
import wikipedia

async def asearch(word, max_results: int = 2):
    async with AsyncDDGS() as ddgs:
        return await ddgs.atext(word, max_results=max_results)

async def duckduck_search_tool(prompts: str):
    prompts = [w.strip() for w in prompts.split(",")] 
    tasks = [asearch(w, 2) for w in prompts]
    results = await asyncio.gather(*tasks)
    items = [item['body'] for result in results for item in result]
    return "\n".join(items)

def wiki_search_tool(search_query: str):
    wikipedia.set_lang("vi")
    try:
        summary = wikipedia.summary(search_query, sentences=17)
        print(summary)
        return summary
    except wikipedia.exceptions.PageError:
        print("Không tìm thấy bài viết với tiêu đề đã cho.")
        return "Không tìm thấy bài viết với tiêu đề đã cho."
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"Có nhiều kết quả phù hợp: {e.options}")
