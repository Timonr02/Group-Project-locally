import asyncio
import os
from asyncua import Client

async def list_nodes():
    """List all available nodes from OPC UA server"""
    url = os.getenv("OPCUA_URL", "opc.tcp://127.0.0.1:4840/laser/")
    
    async with Client(url=url) as client:
        print("Connected to OPC UA Server")
        print("=" * 60)
        
        root = client.get_root_node()
        objects = client.get_objects_node()
        
        print("\nAvailable Nodes:")
        print("-" * 60)
        
        async def print_tree(node, prefix=""):
            try:
                name = await node.read_browse_name()
                node_id = node.nodeid.to_string()
                print(f"{prefix}{name.Name:30} | {node_id}")
                
                children = await node.get_children()
                for child in children:
                    await print_tree(child, prefix + "  ")
            except Exception as e:
                pass
        
        await print_tree(objects)
        print("\n" + "=" * 60)
        print("Copy the Node IDs into NODE_MAPPING environment variable")

if __name__ == "__main__":
    asyncio.run(list_nodes())
