import unittest2
from server import BenchServer
import time
from threading import Thread

class TestServer(unittest2.TestCase):
    def test_all_methods(self):
        bench_server = BenchServer(14021)
        bench_server.start("id")
        bench_server.heartbeat("id")
        bench_server.nextfile("id", "file")
        bench_server.perf("id", 1, 1)
        bench_server.done("id")
        bench_server._print_report()

        # verify
        with open('bench.log', 'r') as content_file:
            content = content_file.read()
            self.assertTrue('started' in content)
            self.assertTrue('alive' in content)
            self.assertTrue('next file' in content)
            self.assertTrue('cpu=1 mem=1' in content)
            self.assertTrue('done' in content)
            self.assertTrue('id: completed=True avg cpu=1, avg_mem=1' in content)

    def test_timeout(self):
        bench_server = BenchServer(14021, 4)
        bench_server.start("id")
        time.sleep(4)
        bench_server._watchdog()

        with open('bench.log', 'r') as content_file:
            content = content_file.read()
            self.assertTrue("id: is dead" in content)
            self.assertTrue("completed=False" in content)

if __name__ == '__main__':
    unittest2.main()