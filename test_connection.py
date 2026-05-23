import asyncio

from iot_gateway.iot_gateway import IoTGateway


config = {
    "server_url": "opc.tcp://ece-p206-rugged:61510/ABB.IoTGateway",
    "app_uri": "urn:freeopcua:client",
    "server_uri": "urn:ece-p206-rugged:ABB:Robotics:IoTGateway",
    "host_name": "ece-p206-rugged",
    "use_security": True,
    "max_search_depth": 12,
}


async def main():
    gateway = IoTGateway(config)

    try:
        await gateway.start()

        print("Connection test passed.")

        node_names = [
            "robotName",
            "robotID",
            "offset",
            "moveRequest",
            "moveDone",
            "moveStatus",
        ]

        for name in node_names:
            node = await gateway.find_node_name(name)

            if node is None:
                print(name, "not found")
            else:
                value = await gateway.read_value(node)
                print(name, "found. Current value:", value)

    finally:
        await gateway.stop()


asyncio.run(main())