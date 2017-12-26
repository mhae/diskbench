# diskbench

To start the server at port 9000:
python server.py 9000

To start a client:
python client.py localhost 9000 11 --label foo 

Client usage:

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
  
