# ABB IoT Gateway Python Client

This README covers only the Python client setup. ABB IoT Gateway installation, alias setup, UserID setup, server restart, logs, and certificate trust steps are in [IoT_Gateway_setup.pdf](https://docs.google.com/document/d/1i3LW3nkOK1fSVOEwlochxpxlMHZINrTRNiXYX8Rr2Ns/edit?usp=sharing).

Security used by the client:

```text
Security Policy: Basic256Sha256
Security Mode  : SignAndEncrypt
Encoding       : Binary
```

## Project structure

```text
├── iot_gateway/
│   └── iot_gateway.py
├── test_connection.py
├── read_write_variables.py
└── send_offset.py
```

## Create virtual environment

Create environment and install asyncua
```cmd
pip install asyncua
```

## Client config

Update this in each script with correct IP[check IOT gateway for the OPC server IP and port]:

```python
config = {
    "server_url": "opc.tcp:///192.168.1.20:61510/ABB.IoTGateway",
    "app_uri": "urn:freeopcua:client",
    "server_uri": "urn:192.168.1.20:ABB:Robotics:IoTGateway",
    "host_name": "192.168.1.20",
    "use_security": True,
    "max_search_depth": 12,
}
```

## Certificate note

Use OpenSSL to create certifcates for connecting to IOT gateway
```cmd
openssl genrsa -out private_key.pem 2048
openssl req -x509 -days 365 -new -out certificate.pem -key private_key.pem -config config/opcuacert.conf
openssl x509 -outform der -in certificate.pem -out certificate.der
```

Place these inside the iot_gateway folder
```text
certificate.der
private_key.pem
```

The first connection may fail because the IoT Gateway rejects the new client certificate. In IoT Gateway, move the certificate from rejected to trusted, save, restart the server, and run the script again.

## Asyncua BadServerUri workaround

Some AsyncUA versions may fail with a `BadServerUri` error even when the endpoint, certificate, and security settings are correct.

If this happens, edit this file inside your virtual environment.

```text
venv\Lib\site-packages\asyncua\client\client.py
```

Find this line around line `501`:

```python
params.ServerUri = f"urn:{self.server_url.hostname}{self.server_url.path.replace('/', ':')}"
```

Change it to:

```python
params.ServerUri = None
```

Save the file and run the Python script again.

## RAPID variables

The scripts use:

```text
offset
robotName
robotID
moveRequest
moveDone
moveStatus
```

`offset` format:

```text
[x_mm, y_mm, z_mm, rx_deg, ry_deg, rz_deg]
```

The Python script writes `offset` and sets `moveRequest=True`. RAPID reads the command, resets `moveRequest=False`, moves the robot, and updates `moveDone` and `moveStatus`.

## Sample scripts
The follwing example scripts are provided in this repoitory:

Test connection:

```cmd
python test_connection.py
```

read/write variables:

```cmd
python read_write_variables.py
```

Send offset from user input:

```cmd
python send_offset.py
```

Example offset input:

```text
10 0 0 0 0 0
```

This sends a 10 mm X offset.



-----------------------------------------------------------------------------
