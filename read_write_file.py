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

        robot_name = await gateway.read_value("robotName")
        robot_id = await gateway.read_value("robotID")
        old_offset = await gateway.read_value("offset")
        move_done = await gateway.read_value("moveDone")
        move_status = await gateway.read_value("moveStatus")

        print("Robot name:", robot_name)
        print("Robot ID:", robot_id)
        print("Current offset:", old_offset)
        print("Move done:", move_done)
        print("Move status:", move_status)

        new_offset = [0, 0, 0, 0, 0, 0]

        print("Writing new offset:", new_offset)

        await gateway.write_float_array("offset", new_offset)

        readback_offset = await gateway.read_value("offset")

        print("Offset after write:", readback_offset)

        # Keep request false so this script does not move the robot
        await gateway.write_bool("moveRequest", False)

        request_state = await gateway.read_value("moveRequest")
        print("moveRequest:", request_state)

    finally:
        await gateway.stop()


asyncio.run(main())