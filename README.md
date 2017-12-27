# diskbench

To start the server at port 9000:

`  python server.py 9000`

The server writes to results to the `bench.log` file.

To start a client for 11 seconds connecting to localhost:9000 and using "foo" as part of the id. Note, the client writes to `/tmp/bench`.

`  python client.py localhost 9000 11 --label foo` 

Client usage:
```
usage: client.py [-h] [--label LABEL] [--chunk CHUNK] [--size SIZE]
                 server port duration

positional arguments:
  server         Server IP or name
  port           Server port
  duration       Duration in seconds (must be > 10)
  

optional arguments:
  -h, --help     show this help message and exit
  --label LABEL  Label for this client
  --chunk CHUNK  Chunk size in MB
  --size SIZE    File size in MB
  ```
  
Unit tests:

`  python client_tests.py`

`  python server_tests.py`
