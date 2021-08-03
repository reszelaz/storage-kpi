import timeit
import argparse
import threading
import traceback
from taurus.core.util.log import Logger
from taurus.core.util.threadpool import ThreadPool


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


class JobDone:
    
    def __init__(self):
        self._event = threading.Event()
    
    def set(self, _):
        self._event.set()
    
    def wait(self):
        self._event.wait()

def job():
    pass


class Worker(threading.Thread, Logger):
            
    def __init__(self, job, callback, th_id, stack, *args, **kwargs):                
        name = self.__class__.__name__
        threading.Thread.__init__(self, name=name)
        Logger.__init__(self, name)
        self.job = job
        self.callback = callback
        self.th_id = th_id
        self.stack = stack
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            self.callback(self.job(*self.args, **self.kwargs))
        except:
            orig_stack = "".join(traceback.format_list(self.stack))
            self.error(
                "Uncaught exception running job '%s' called "
                "from thread %s:\n%s",
                self.job.__name__,
                self.th_id,
                orig_stack,
                exc_info=1,
            )


class RunThreadPool:

    def __init__(self, Psize=10):
        self.executor = ThreadPool(Psize=Psize)
        
    def run(self):        
        job_done = JobDone()
        self.executor.add(job, job_done.set)
        job_done.wait()


def run_thread_pool_with_join(Psize):
    executor = ThreadPool(Psize=Psize)
    job_done = JobDone()
    executor.add(job, job_done.set)
    job_done.wait()
    executor.join()

def run_thread():
    th_id, stack = threading.currentThread().name, traceback.extract_stack()[:-1]
    job_done = JobDone()
    worker = Worker(job, job_done.set, th_id, stack)
    worker.start()
    job_done.wait()
    worker.join()
    worker = None


def main():
    parser = argparse.ArgumentParser(description="taurus ThreadPool benchmark")
    parser.add_argument("-n, ", "--number", metavar="number", type=int, nargs="?",
                        required=True, default=100, help="Number of runs")
    parser.add_argument("-e, ", "--executor", metavar="executor", type=str, nargs="?",
                        required=True, default="pool", help="Executor to use: thread_pool_with_join, thread_pool, thread")
    args = parser.parse_args()
    number = args.number
    executor = args.executor
    print("Run {} times".format(number))
    if executor == "thread_pool_with_join":
        Psize = 1
        print("Run ThreadPool (Psize={}) with join".format(Psize))
        setup = "from thread_benchmark import run_thread_pool_with_join"
        stmt = "run_thread_pool_with_join({})".format(Psize)
    elif executor == "thread_pool":
        Psize = 10
        print("Run ThreadPool (Psize={}) without join".format(Psize))
        setup = ("from thread_benchmark import RunThreadPool;"
                 "benchmark=RunThreadPool(Psize={})").format(Psize)
        stmt = "benchmark.run()"
    elif executor == "thread":
        print("Run Thread")
        setup = "from thread_benchmark import run_thread"
        stmt = "run_thread()"
    else:
        raise argparse.ArgumentError("unknown executor arg")
    mean_time = timeit.timeit(setup=setup, stmt=stmt, number=number) / number
    print("Mean time: {}".format(mean_time))


if __name__ == "__main__":
    main()
