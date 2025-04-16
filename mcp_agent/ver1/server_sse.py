from mcp.server.fastmcp import FastMCP, Image, Context
from mcp.server.fastmcp.prompts import base
from dotenv import load_dotenv
load_dotenv()
import json
import os
import httpx
from bs4 import BeautifulSoup
from PIL import Image as PILImage 
import io

mcp = FastMCP("First MCP server SSE")

SERPER_URL='https://google.serper.dev/search'

async def search_web(query: str):
    payload = json.dumps({
        "q": query, 'num': 2
    })
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SERPER_URL, headers=headers, data=payload, timeout=30)
            # print("\nresponse:::: ", response.text)
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}

async def fetch_url(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url=url, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            # print(text)
            return text
        except httpx.TimeoutException:
            return "Timeout error"

@mcp.tool()
async def get_docs(query: str):
    """
    Tìm kiếm thông tin trên Internet.
    
    Tham số:
        query: câu hỏi cần tìm kiếm.
    Trả về:
        Nội dung sau khi tìm kiếm.
    """
    results = await search_web(query=query)
    text = ""
    for result in results['organic']:
        text += await fetch_url(result['link'])
    return text
 
@mcp.tool()
def multiply(a:int, b: int):
    """
    Multiply two numbers
    """
    return a*b

@mcp.tool()
def sum(a:int, b: int):
    "Sum two numbers"
    return a + b






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.sse_app(), host="127.0.0.1", port=1234)
    # # Initialize and run the server
    # mcp.run(transport='sse')  #Default port 8000
