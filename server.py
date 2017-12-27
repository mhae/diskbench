from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer
import sys
import argparse
import SocketServer
import time
from threading import Thread, Lock
import logging

# Not sure about the exact threading semantics of the RPC server... (revist)
class SimpleThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer):
        pass

class ClientInfo:
    """ Class representing currently connected client info """
    def __init__(self, id):
        self.id = id
        self.last_heartbeat = time.time()
        self.done = False
        self.aborted = False # True if client missed a couple of heartbeats
        # Sums for average reporting ... TODO: running average
        self.sum_cpu = 0
        self.sum_mem = 0.0
        self.sum_count = 0

    def avg_cpu(self):
        """ Avg CPU util in % or 0 if N/A """
        if self.sum_count == 0:
            return 0
        return self.sum_cpu/self.sum_count 

    def avg_mem(self):
        """ Avg rss in bytes or 0 if N/A """
        if self.sum_count == 0:
            return 0
        return self.sum_mem/self.sum_count 

class BenchServer:
    ci_mutex = Lock()
    def __init__(self, port, unresponsive_client_timeout = 2*10):
        self.port = port
        self.client_info = {}
        self.rpc_server = None
        self.unresponsive_client_timeout = unresponsive_client_timeout
        logging.basicConfig(filename='bench.log', filemode='w', level=logging.INFO, format='%(asctime)s %(message)s')

    def start(self, id):
        """ RPC method to indicate start """
        logging.info("%s: started", id)
        with self.ci_mutex:
            self.client_info[id] = ClientInfo(id) # TODO: Error checking if already exists
        return True

    def done(self, id):
        """ RPC method to indicate stop """
        logging.info("%s: done", id)
        with self.ci_mutex:
            ci = self.client_info[id]
            ci.done = True
        return True

    def nextfile(self, id, file):
        """ RPC method to indicate roll over to next file """
        logging.info("%s: next file %s", id, file) 
        return True

    def perf(self, id, cpu, mem):
        """ RPC method to log perf stats """
        logging.info("%s: cpu=%d mem=%d", id, cpu, mem)
        with self.ci_mutex:
            ci = self.client_info[id]
            ci.sum_cpu += cpu
            ci.sum_mem += mem
            ci.sum_count += 1
        return True

    def heartbeat(self, id):
        """ RPC method to indicate that client is still alive """
        logging.info("%s: alive", id)
        with self.ci_mutex:
            ci = self.client_info[id]
            ci.last_heartbeat = time.time()
        return True

    def _print_report(self):
        """ Print the final report """
        # Assumes locked client_info
        logging.info("Report:")
        for ci in self.client_info.itervalues():
            logging.info("%s: completed=%s avg_cpu=%d, avg_mem=%d", ci.id, not ci.aborted, ci.avg_cpu(), ci.avg_mem())

    def _watchdog(self):
        """ Watchdog for client termination and aborts """
        while True:
            with self.ci_mutex:
                if len(self.client_info) > 0:
                    all_done = True
                    now = time.time() 
                    for ci in self.client_info.itervalues():
                        # print "Checking: %s" % ci.id
                        # Check for timed out clients
                        if ci.aborted is False and now-ci.last_heartbeat > self.unresponsive_client_timeout:
                            logging.warning("%s: is dead", ci.id)
                            ci.done = True
                            ci.aborted = True

                        if ci.done == False:
                            all_done = False
                            break

                    if all_done:
                        # Report and terminate
                        self._print_report()
                        self.shutdown()
                        # sys.exit(0)
                        return

            time.sleep(2)        
        

    def shutdown(self):
        if self.rpc_server is not None:
            self.rpc_server.shutdown()

    def run(self):
        self.rpc_server = SimpleThreadedXMLRPCServer(("", self.port), logRequests=False)
        self.rpc_server.register_instance(self)

        watchdog = Thread(target = self._watchdog)
        watchdog.setDaemon(1)
        watchdog.start()

        self.rpc_server.serve_forever()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    args = parser.parse_args()
    bench_server = BenchServer(args.port)
    bench_server.run()

if __name__ == '__main__': main()