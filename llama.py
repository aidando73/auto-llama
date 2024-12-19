from llama_stack_client.lib.direct.direct import LlamaStackDirectClient
import asyncio

async def main():
    client = await LlamaStackDirectClient.from_template('fireworks')
    await client.initialize()

if __name__ == "__main__":
    asyncio.run(main())
