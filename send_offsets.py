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


def get_offset_from_user():
    print()
    print("Enter offset values:")
    print("x y z rx ry rz")
    print("Example:")
    print("10 0 0 0 0 0")
    print()

    text = input("Offset: ").strip()
    parts = text.split()

    if len(parts) != 6:
        raise ValueError("You must enter exactly 6 values: x y z rx ry rz")

    offset = []

    for item in parts:
        offset.append(float(item))

    return offset


async def wait_until_done(gateway):
    while True:
        move_done = await gateway.read_value("moveDone")
        move_status = await gateway.read_value("moveStatus")

        print("moveDone:", move_done, "moveStatus:", move_status)

        if move_done is True:
            print("Robot reached target.")
            return

        if move_status == -1:
            print("Robot reported an error.")
            return

        await asyncio.sleep(0.1)


async def main():
    gateway = IoTGateway(config)

    try:
        await gateway.start()

        robot_name = await gateway.read_value("robotName")
        robot_id = await gateway.read_value("robotID")

        print("Connected robot:", robot_name)
        print("Robot ID:", robot_id)

        offset = get_offset_from_user()

        print("Sending offset:", offset)

        await gateway.write_float_array("offset", offset)

        readback = await gateway.read_value("offset")
        print("Offset readback:", readback)

        await gateway.write_bool("moveRequest", True)

        print("Move request sent.")

        await wait_until_done(gateway)

    finally:
        await gateway.stop()


asyncio.run(main())