# Control Panel v2

## Installation and running
```bash
pip3 install -r requirements.txt
bash setup.sh
....
python3 slave.py configs.json 
```
## Configurations


Store configurations in a json file in the following format
```json
[
  {"key": "master_ip", "value": "127.0.0.1"},
  {"key": "cp_port", "value": "80"}
]
```
|Key|Description|type|default|required|
|----------------|---------|----------------------|-----------------------------|----
|`master_ip`|IP for master server|`str`|`null`| yes
|`master_port`|Port for master server|`int`|`5600`| yes
|`cp_ip`|Control Panel webserver IP, possible values include `"localhost"`|`str`|`0.0.0.0`| yes
|`cp_port`|Control Panel webserver port|`int`|`7000`| yes
|`master_db_engine` | DB engine type (ie mysql, sqlite3) |`str`|`mysql`| yes
|`master_db_address`|Database address or file path (if sqlite3)| `str`|`null`|yes
