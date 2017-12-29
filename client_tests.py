import unittest2
from threading import Thread, Event
from client import Worker, CpuMemCollector, Heartbeat
import time
import os

class ServerProxy:
    """ Mock """
    def __init__(self):
        self.nextfile_cnt = 0
        self.start_cnt = 0
        self.done_cnt = 0
        self.perf_cnt = 0
        self.heartbeat_cnt = 0

    def nextfile(self, id, file):
        self.nextfile_cnt += 1

    def start(self, id):
        self.start_cnt += 1

    def done(self, id):
        self.done_cnt += 1

    def heartbeat(self, id):
        self.heartbeat_cnt += 1

    def perf(self, id, cpu, mem):
        self.perf_cnt += 1
        # CPU util is difficult to test ... would need to run a CPU hog but we can assume that psutil functions work properly
        # Therefore, we're just counting the method

class TestWorker(unittest2.TestCase):
    def test_happy_path(self):
        pill2kill = Event()
        server_proxy = ServerProxy()

        worker = Worker(pill2kill, server_proxy, "myid", "test", 1024, 4096, None)
        worker._write_chunks(1)
        self.assertEqual(4096, os.path.getsize('/tmp/bench/test/1'))
        self.assertEqual(1, server_proxy.nextfile_cnt)

class TestHeartbeat(unittest2.TestCase):
    # """ This is almost a functional test since it is running ~7 """
    # TODO: optimize this test
    def test_happy_path(self):
        pill2kill = Event()
        server_proxy = ServerProxy()

        heartbeat = Heartbeat(pill2kill, server_proxy, "myid")
        heartbeat_thread = Thread(target=heartbeat.run)
        heartbeat_thread.setDaemon(1)
        heartbeat_thread.start()

        time.sleep(7)
        pill2kill.set()
        heartbeat_thread.join()
        self.assertTrue(server_proxy.heartbeat_cnt >= 1)

class TestCpuMemCollector(unittest2.TestCase):

    # """ This is almost a functional test since it is running ~10s """
    # TODO: optimize this test
    def test_happy_path(self):
        pill2kill = Event()
        server_proxy = ServerProxy()

        cpu_mem_collector = CpuMemCollector(pill2kill, server_proxy, "myid", os.getpid())
        cpu_mem_collector_thread = Thread(target=cpu_mem_collector.run)
        cpu_mem_collector_thread.setDaemon(1)
        cpu_mem_collector_thread.start()

        time.sleep(4)
        pill2kill.set()
        cpu_mem_collector_thread.join()
        self.assertTrue(server_proxy.perf_cnt >= 1)

if __name__ == '__main__':
    unittest2.main()