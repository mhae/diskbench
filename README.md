# diskbench

## Requirements
`sudo pip install psutil`

`sudo pip install unittest2`

(To install pip on Ubuntu 14.04: `sudo apt-get install python-pip python-dev build-essential`)

## Running

To start the server at port 9000:

`  python server.py 9000`

The server writes the results to the `bench.log` file in the current directory.

To start a client for 11 seconds connecting to localhost:9000 and using "foo" as part of the id: 

`  python client.py localhost 9000 11 --label foo` 

Note, the client writes to `/tmp/bench` by default.

Client usage:
```
usage: client.py [-h] [--label LABEL] [--chunk CHUNK] [--size SIZE] server port duration

positional arguments:
  server         Server IP or name
  port           Server port
  duration       Duration in seconds (must be > 1)
  

optional arguments:
  -h, --help     show this help message and exit
  --label LABEL  Label for this client
  --chunk CHUNK  Chunk size in MB
  --size SIZE    File size in MB
  --out dir      Target directory (/tmp if omitted)   
  ```
  
## Unit tests:

`  python client_tests.py`

`  python server_tests.py`
