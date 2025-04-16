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

mcp = FastMCP("First MCP server")

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



# @mcp.resource("resourceTinh://app_ne")
# def get_config():
#     """Static configuration data"""
#     return "App configuration resource tĩnh"

# @mcp.resource("resourceDong://user_id/{user_id}")
# def get_user_profile(user_id: str):
#     """Dynamic resource"""
#     return f"Profile data for user {user_id} nayy"

# @mcp.prompt()
# def prompt_template_agent(role: str):
#     return f"bạn là một {role} với 20 năm kinh nghiệm"

# @mcp.prompt()
# def debug_error(error: str):
#     return [
#         base.UserMessage("Tôi đang gặp lỗi này:"),
#         base.UserMessage(error),
#         base.AssistantMessage("Tôi sẽ giúp bạn sữa lỗi đó.")
#     ]

# @mcp.tool()
# def handle_image_data(image_path: str):
#     image = PILImage.open(image_path)
#     buffer = io.BytesIO()
#     image.save(buffer, format='png')
#     return Image(data=buffer.getvalue(), format="png")

# @mcp.tool()
# async def long_task(files: list[str], ctx: Context) -> str:
#     """Process multiple files with progress tracking"""
#     for i, file in enumerate(files):
#         ctx.info(f"Processing {file}")
#         await ctx.report_progress(i, len(files))
#         data, mime_type = await ctx.read_resource(f"file://{file}")
#     return "Processing complete"









if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
