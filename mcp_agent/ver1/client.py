import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv
load_dotenv()
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from autogen_agentchat.agents import AssistantAgent
from azure.core.credentials import AzureKeyCredential
from autogen_ext.models.azure import AzureAIChatCompletionClient
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from pathlib import Path
from autogen_core.tools import FunctionTool



class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = AzureAIChatCompletionClient(
            model="gpt-4.1",                  ##   
            # model='gpt-4o',                       ##    
            endpoint="https://models.inference.ai.azure.com",
            credential=AzureKeyCredential(os.getenv('GITHUB_TOKEN')),
            model_info={
                "json_output": True,
                "function_calling": True,
                "vision": False,
                "family": "unknown",
                "structured_output": False  
            }
        )
    
    async def connect_to_server(self, server_script_path: str):
        server_params = StdioServerParameters(
            command='python',
            args=[server_script_path],
            env=None
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        # result = await self.session.call_tool(name='sum', arguments={'a':"17", 'b':"03"})
        # print("--result--: ", result)

    async def process_query(self, query:str):
        # Setup server params for local filesystem access
        server_params = StdioServerParams(
            command=r"D:\.thuctap\tma\code\mcp_agent\mcp-server-demo\.venv\Scripts\python.exe", args=[r"D:\.thuctap\tma\code\mcp_agent\mcp-server-demo\server.py", "--transport", "stdio"]
        )
        # Get all available tools from the server
        tools = await mcp_server_tools(server_params)
        # tool = FunctionTool(self.sum, description="To sum two numbers")
        for tool in tools:
            print("\ntools: ", tool.schema)

        agent = AssistantAgent(
            name="Assistant",
            model_client=self.client,
            tools=tools,
            system_message='Use tools to solve tasks.'
        )
        
        result = await agent.run(task=query)
        print(result.messages)
        return result.messages[-1].content


    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python client.py <path_to_server_script>")
    #     sys.exit(1)
    # print("sys.argv[1]: ", sys.argv[1])
    client = MCPClient()
    try:
        # await client.connect_to_server(sys.argv[1])
        while True:
            try:
                query = input("\nNhập vào câu hỏi: ").strip()
                if query.lower() == 'q':
                    break

                respose = await client.process_query(query=query)
                print("\n", respose)

            
            except Exception as e:
                await client.cleanup()
                print(f"Error : {str(e)}")
    finally:
        await client.cleanup()
        print("Client cleanup() DONE")

if __name__ == "__main__":
    asyncio.run(main())



