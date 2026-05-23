# utils/iot_gateway.py

from pathlib import Path

from asyncua import Client, ua


class IoTGateway:
    """
    Simple asyncua client for connecting to an IoT Gateway.

    Main functions:
        start()
        stop()
        find_node_name()
        read_value()
        write_value()
    """

    def __init__(self, config=None):
        if config is None:
            config = {}

        self.server_url = config.get(
            "server_url",
            "opc.tcp://ece-p206-rugged:61510/ABB.IoTGateway"
        )

        self.app_uri = config.get(
            "app_uri",
            "urn:freeopcua:client"
        )

        self.server_uri = config.get(
            "server_uri",
            "urn:ece-p206-rugged:ABB:Robotics:IoTGateway"
        )

        self.host_name = config.get(
            "host_name",
            "ece-p206-rugged"
        )

        self.security_policy = config.get(
            "security_policy",
            "Basic256Sha256"
        )

        self.security_mode = config.get(
            "security_mode",
            "SignAndEncrypt"
        )

        self.use_security = config.get("use_security", True)
        self.max_search_depth = config.get("max_search_depth", 12)

        script_dir = Path(__file__).resolve().parent

        self.cert_path = Path(
            config.get("cert_path", script_dir / "certificate.der")
        )

        self.key_path = Path(
            config.get("key_path", script_dir / "private_key.pem")
        )

        self.client = None
        self.connected = False

        # stores found nodes so we do not search again and again
        self.nodes = {}

    
    # ------------------------------------------------------------
    # start / stop
    # ------------------------------------------------------------

    async def start(self):
        if self.connected:
            return

        self.client = Client(self.server_url)
        self.client.application_uri = self.app_uri
        self.client.server_uri = self.server_uri

        if self.use_security:
            security_string = (
                f"{self.security_policy},"
                f"{self.security_mode},"
                f"{self.cert_path},"
                f"{self.key_path}"
            )

            await self.client.set_security_string(security_string)

        await self.client.connect()

        self.connected = True
        print("Connected to IoT Gateway:", self.server_url)

    async def stop(self):
        if self.client is not None and self.connected:
            await self.client.disconnect()

        self.client = None
        self.connected = False
        self.nodes.clear()

        print("Disconnected from IoT Gateway")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    def check_connection(self):
        if self.client is None or not self.connected:
            raise RuntimeError("IoT Gateway is not connected. Call await start() first.")

    # ------------------------------------------------------------
    # node search
    # ------------------------------------------------------------

    async def get_browse_name(self, node):
        try:
            name = await node.read_browse_name()
            return name.Name
        except Exception:
            return None

    async def get_display_name(self, node):
        try:
            name = await node.read_display_name()
            return name.Text
        except Exception:
            return None

    async def find_node_name(self, node_name, start_node=None, max_depth=None, use_cache=True):
        """
        Search the IoT Gateway tree and return the first node
        with this browse name or display name.
        """

        self.check_connection()

        if use_cache and node_name in self.nodes:
            return self.nodes[node_name]

        if start_node is None:
            start_node = self.client.nodes.objects

        if max_depth is None:
            max_depth = self.max_search_depth

        queue = [(start_node, 0)]

        while queue:
            node, depth = queue.pop(0)

            browse_name = await self.get_browse_name(node)
            display_name = await self.get_display_name(node)

            if browse_name == node_name or display_name == node_name:
                self.nodes[node_name] = node
                return node

            if depth >= max_depth:
                continue

            try:
                children = await node.get_children()

                for child in children:
                    queue.append((child, depth + 1))

            except Exception:
                pass

        return None

    async def find_all_node_names(self, node_name, start_node=None, max_depth=None):
        """
        Search and return all nodes with the given name.
        Useful when the same variable exists in multiple robot modules.
        """

        self.check_connection()

        if start_node is None:
            start_node = self.client.nodes.objects

        if max_depth is None:
            max_depth = self.max_search_depth

        matches = []
        queue = [(start_node, 0)]

        while queue:
            node, depth = queue.pop(0)

            browse_name = await self.get_browse_name(node)
            display_name = await self.get_display_name(node)

            if browse_name == node_name or display_name == node_name:
                matches.append(node)

            if depth >= max_depth:
                continue

            try:
                children = await node.get_children()

                for child in children:
                    queue.append((child, depth + 1))

            except Exception:
                pass

        return matches

    # ------------------------------------------------------------
    # read / write
    # ------------------------------------------------------------

    async def read_value(self, node):
        """
        Read value from a node.

        You can pass:
            node object
            node name as string
        """

        self.check_connection()

        if isinstance(node, str):
            node = await self.find_node_name(node)

            if node is None:
                raise RuntimeError("Node not found")

        return await node.read_value()

    async def write_value(self, node, value):
        """
        Write value to a node.

        You can pass:
            node object
            node name as string
        """

        self.check_connection()

        if isinstance(node, str):
            node = await self.find_node_name(node)

            if node is None:
                raise RuntimeError("Node not found")

        await node.write_value(value)

    # ------------------------------------------------------------
    # optional write helpers
    # ------------------------------------------------------------

    async def write_bool(self, node, value):
        """
        Use this if normal write_value does not work for bool nodes.
        """

        self.check_connection()

        if isinstance(node, str):
            node = await self.find_node_name(node)

            if node is None:
                raise RuntimeError("Node not found")

        data = ua.DataValue(
            ua.Variant(bool(value), ua.VariantType.Boolean)
        )

        await node.write_value(data)

    async def write_float(self, node, value):
        """
        Use this if normal write_value does not work for float/num nodes.
        """

        self.check_connection()

        if isinstance(node, str):
            node = await self.find_node_name(node)

            if node is None:
                raise RuntimeError("Node not found")

        data = ua.DataValue(
            ua.Variant(float(value), ua.VariantType.Double)
        )

        await node.write_value(data)

    async def write_float_array(self, node, values):
        """
        Useful for ABB num arrays like:
            gOffset{6}
        """

        self.check_connection()

        if isinstance(node, str):
            node = await self.find_node_name(node)

            if node is None:
                raise RuntimeError("Node not found")

        values = [float(v) for v in values]

        data = ua.DataValue(
            ua.Variant(values, ua.VariantType.Double)
        )

        await node.write_value(data)


async def connect_iot_gateway(config=None):
    gateway = IoTGateway(config)
    await gateway.start()
    return gateway