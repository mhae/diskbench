from xmlrpclib import ServerProxy
import argparse
import socket
from time import sleep
from threading import Thread, Event
import os
import multiprocessing as mp
import psutil
import signal
import sys
import shutil

# TODO
# Error handling when server aborts
# Make target path (base) configurable

class Worker:
    """ The worker writing to files (started in separate process for accurate CPU and mem stat collection """
    kill_now = False
    def __init__(self, stop_event, server_proxy, my_id, label, chunk, size, out):
        self.stop_event = stop_event
        self.server_proxy = server_proxy
        self.my_id = my_id
        self.chunk = chunk
        self.label = label
        self.size = size
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        if out is None:
            out = "/tmp"
        self.base = self._makepath(out+"/bench/")
        self._prep(self.base)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

    def _makepath(self, base):
        """ Returns a path depending on label or pid """
        if self.label is None:
            base += "client.%d/" % os.getpgid()
        else:
            base += "%s/" % self.label 
        return base

    def _prep(self, dir):
        """ Clean up """
        shutil.rmtree(dir, ignore_errors=True)
        os.makedirs(dir)

    def _write_chunks(self, id):
        data = bytearray(self.chunk)
        file_name = self.base+"%d" % id
        file = open(file_name, "w+")
        self.server_proxy.nextfile(self.my_id, file_name)
        print "Writing: %s" % file_name
        current_size = 0
        while self.kill_now is False and current_size < self.size:
            file.write(data)
            current_size += self.chunk
        file.close()

    def work(self):
        """ Work loop, continously creates files based on size and chunk """
        self.server_proxy.start(self.my_id)
        print "Starting"
        id = 1
        while not self.kill_now:
            self._write_chunks(id)
            id = id + 1

        self.server_proxy.done(self.my_id)
        print "Done"

    def run(self):
        proc = mp.Process(target=self.work)
        proc.start()
        return proc

class CpuMemCollector:
    """ Collects CPU and memory stats for the specified work pid """

    def __init__(self, stop_event, server_proxy, my_id, worker_pid):
        self.stop_event = stop_event
        self.server_proxy = server_proxy
        self.my_id = my_id
        self.worker_pid = worker_pid

    def run(self):
        """ Collect cpu and mem until we're told to stop """
        proc = psutil.Process(self.worker_pid)
        # Get some initial values
        cpu, mem = proc.cpu_percent(1), proc.memory_info()
        print cpu, mem
        _ = self.server_proxy.perf(self.my_id, cpu, mem.rss)
        while not self.stop_event.wait(1):
            try:
                cpu, mem = proc.cpu_percent(10), proc.memory_info()
                print cpu, mem
                _ = self.server_proxy.perf(self.my_id, cpu, mem.rss)
            except:
                pass # Suppress suprious exceptions when child terminates

class Heartbeat:
    """ Sends a heartbeat every 5s to the server """
    def __init__(self, stop_event, server_proxy, my_id):
        self.stop_event = stop_event
        self.server_proxy = server_proxy
        self.my_id = my_id

    def run(self):
        """ Send hearbeat very 5s """
        while not self.stop_event.wait(5):
            _ = self.server_proxy.heartbeat(self.my_id)
            


class BenchClient:
    """ Client driver """

    assumed_disk_tput = 50*1024*1024 # 50MB/s

    def __init__(self, server, port, duration, label=None, chunk=None, size=None, out=None):
        self.port = port
        self.server = server
        self.label = label
        self.duration = duration
        self.my_id = "%s[%s]" % (socket.gethostbyname(socket.gethostname()),label)
        if chunk is None:
            chunk = 10
        if size is None:
            size = chunk * 4
        self.chunk = chunk*1024*1024
        self.size = size*1024*1024
        if out is None:
            out = "/tmp"
        self.out = out

    def start(self):
        # Sanity checks
        if self.duration <= 1:
            raise ValueError("Duration must be greater than 1s")
        # Assuming 50MB/s write speed, sanity check the duration against the chunk size
        if self.duration < self.chunk*2/self.assumed_disk_tput:
            raise ValueError("Duration must be least %ds for specified chunk size" % (self.chunk*2/self.assumed_disk_tput)) 

        # Config
        pill2kill = Event()

        server_proxy = ServerProxy("http://%s:%s" % (self.server, self.port))

        worker = Worker(pill2kill, server_proxy, self.my_id, self.label, self.chunk, self.size, self.out)
        worker_proc = worker.run()

        heartbeat = Heartbeat(pill2kill, server_proxy, self.my_id)
        heartbeat_thread = Thread(target=heartbeat.run)
        heartbeat_thread.setDaemon(1)
        heartbeat_thread.start()

        cpu_mem_collector = CpuMemCollector(pill2kill, server_proxy, self.my_id, worker_proc.pid)
        cpu_mem_collector_thread = Thread(target=cpu_mem_collector.run)
        cpu_mem_collector_thread.setDaemon(1)
        cpu_mem_collector_thread.start()

        try:
            sleep(self.duration)
            pill2kill.set()
            worker_proc.terminate()
        except KeyboardInterrupt:
            pill2kill.set()
            worker_proc.terminate()
        cpu_mem_collector_thread.join()
       

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("server", help="Server IP or name")
    parser.add_argument("port", help="Server port")
    parser.add_argument("duration", type=int, help="Duration in seconds (must be > 10)")
    parser.add_argument("--label", help="Label for this client")
    parser.add_argument("--chunk", type=int, help="Chunk size in MB")
    parser.add_argument("--size", type=int, help="File size in MB")
    parser.add_argument("--out", help="Target directory for output files")
    args = parser.parse_args()
    bench_client = BenchClient(args.server, args.port, args.duration, args.label, args.chunk, args.size, args.out)
    bench_client.start()

if __name__ == '__main__': main()
