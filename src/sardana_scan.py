import time
import math
import queue
import psutil
import random
import datetime
import threading
import os
import argparse
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from sardana.sardanautils import is_non_str_seq
from sardana.sardanathreadpool import get_thread_pool
from sardana.macroserver.recorders.storage import SPEC_FileRecorder
from sardana.macroserver.scan import ColumnDesc
from sardana.macroserver.scan.scandata import RecordList, DataHandler


DESCRIPTION = "Storage Performance Indicator Measurement"

executor = None

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


class Scan(object):

    def __init__(self, file_, nb_of_columns=(20, 0, 0), nb_of_points=100,
                 integ_time=.1, pandas=False):
        self.file = file_
        if not is_non_str_seq(nb_of_columns):
            self.nb_of_scalars = nb_of_columns
            self.nb_of_spectrums = 0
            self.nb_of_images = 0
        else:
            self.nb_of_scalars = nb_of_columns[0]
            self.nb_of_spectrums = nb_of_columns[1]
            self.nb_of_images = nb_of_columns[2]
        self.nb_of_points = nb_of_points
        self.integ_time = integ_time
        self.record_list = None
        self.environ = dict()
        self._pandas = pandas

    def _prepare_environ(self):
        self.environ = dict()
        self.environ["startts"] = ts = time.time()
        self.environ["starttime"] = datetime.datetime.fromtimestamp(ts)
        self.environ["serialno"] = 0
        data_desc = list()
        data_desc.append(ColumnDesc(name="point_nb",
                                    label="#Pt No",
                                    dtype="int64"))
        for i in range(self.nb_of_scalars):
            data_desc.append(ColumnDesc(name="spectrum%d" % i,
                                        label="spectrum%d" % i,
                                        dtype="float64"))
        for i in range(self.nb_of_spectrums):
            data_desc.append(ColumnDesc(name="spectrum%d" % i,
                                        label="spectrum%d" % i,
                                        dtype="(float64, )"))
        for i in range(self.nb_of_images):
            data_desc.append(ColumnDesc(name="image%d" % i,
                                        label="image%d" % i,
                                        dtype="((float64, ), )"))
        data_desc.append(ColumnDesc(name="timestamp",
                                    label="dt",
                                    dtype="float64"))
        self.environ["datadesc"] = data_desc
        self.environ["title"] = DESCRIPTION
        self.environ["user"] = "sicilia"

    def start(self):
        spec_recorder = SPEC_FileRecorder(self.file)
        data_handler = DataHandler()
        data_handler.addRecorder(spec_recorder)
        self._prepare_environ()
        if self._pandas:
            import pandas as pd
            class PandasRecordList:

                def __init__(self, datahandler, environ=None, apply_interpolation=False,
                            apply_extrapolation=False, initial_data=None):
                    self.datahandler = datahandler
                    self.environ = environ
                    self.records = None
                
                def getEnvironValue(self, name):
                    return self.environ[name]

                def getEnviron(self):
                    return self.environ
                
                def start(self):
                    columns = [dd.name for dd in self.environ["datadesc"]]
                    self.records = pd.DataFrame(columns=columns)
                    self.datahandler.startRecordList(self)


                def addRecord(self, record):
                    self.records = self.records.append(record, ignore_index=True)

                def end(self):
                    self.datahandler.endRecordList(self)
                    self.records = None

            self.record_list = PandasRecordList(data_handler,
                                                self.environ)
        else:
            self.record_list = RecordList(data_handler,
                                          self.environ)
        self.record_list.start()

    def _acquire(self, point_nb):
        time.sleep(self.integ_time)
        data_line = dict()
        data_line["point_nb"] = point_nb
        for col in range(self.nb_of_scalars):
            value = random.random() * random.randint(1, 10)
            data_line["scalar%d" % col] = value
        for col in range(self.nb_of_spectrums):
            value = np.ones(1024, ) * random.random()
            data_line["spectrum%d" % col] = value
        for col in range(self.nb_of_images):            
            value = np.ones((1024, 1024)) * random.random()
            data_line["image%d" % col] = value
        timestamp = point_nb * random.random()
        data_line["timestamp"] = timestamp
        return data_line

    def run(self):
        for point_nb in range(self.nb_of_points):
            data_line = self._acquire(point_nb)
            self.record_list.addRecord(data_line)

    def end(self):
        self.environ["endts"] = ts = time.time()
        self.environ["endtime"] = datetime.datetime.fromtimestamp(ts)
        self.record_list.end()

def scan(file_, pandas=False):
    print("Scan run in {}".format(threading.get_ident()))
    scan = Scan(file_, 
                nb_of_columns=(20, 0, 1),
                integ_time=0.001,
                pandas=pandas)
    scan.start()
    scan.run()
    scan.end()


def scan_thread(file_, pandas=False):
    global executor
    if executor is None:
        class Executor(threading.Thread):
            def __init__(self):                
                super().__init__()
                self.daemon = True
                self._queue = queue.Queue()
            
            def run(self):
                while True:
                    job, callback, args = self._queue.get()
                    if job is None:
                        break
                    callback(job(*args))
            
            def add(self, job, callback, *args):
                self._queue.put((job, callback, args))
            
            def join(self):
                self._queue.put((None, None, None))
                super().join()

        executor = Executor()
        executor.start()    

    scan_done = ScanDone()
    executor.add(scan, scan_done.set, file_, pandas)
    scan_done.wait()


def scan_taurus_thread_pool(file_, pandas=False):
    global executor
    if executor is None:
        from taurus.core.util.threadpool import ThreadPool
        executor = ThreadPool(Psize=10, daemons=True)
    scan_done = ScanDone()
    executor.add(scan, scan_done.set, file_, pandas)
    scan_done.wait()


def scan_concurrent_thread_pool(file_, pandas=False):
    global executor
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=10)
    future = executor.submit(scan, file_, pandas)
    future.result()

class ScanDone:
    
    def __init__(self):
        self._event = threading.Event()
    
    def set(self, _):
        self._event.set()
    
    def wait(self):
        self._event.wait()


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("-f, ", "--file", metavar="file", type=str, nargs="?",
                        required=True, help="File to store the scan data")
    parser.add_argument("-r, ", "--repeat", metavar="repeat", type=int, nargs="?",
                        required=False, default=1, help="Number of scan repeats")
    parser.add_argument("-t, ", "--threaded", metavar="threaded", type=str, nargs="?",
                        required=False, default="no", help="Run scan in threads using: thread, concurrent, taurus")
    parser.add_argument("-p, ", "--pandas", metavar="pandas", type=str2bool, nargs="?",
                        required=False, default=False, help="Use pandas implementation of RecordList")
    parser.add_argument("-j, ", "--join", metavar="join", type=bool, nargs="?",
                        required=False, default=False, help="Join/Shutdown executor (if any) and call gc.collect()")
    args = parser.parse_args()
    file_ = args.file
    repeat = args.repeat
    threaded = args.threaded
    pandas = args.pandas
    join = args.join
    process = psutil.Process(os.getpid())
    for i in range(repeat):
        print("repeat #{}".format(i+1))
        print(
            "RSS before scan: {}".format(
                convert_size(process.memory_info().rss)
                )
            )
        if threaded == "taurus":
            scan_taurus_thread_pool(file_, pandas)
        elif threaded == "concurrent":
            scan_concurrent_thread_pool(file_, pandas)
        elif threaded == "thread":
            scan_thread(file_, pandas)
        elif threaded == "no":
            scan(file_, pandas)
        else:
            raise argparse.ArgumentError("unknown argument threaded")
        print(
            "RSS after scan: {}".format(
                convert_size(process.memory_info().rss)
                )
            )
    if join:
        global executor
        if executor is not None:
            try:
                executor.join()
            except AttributeError:
                executor.shutdown()
            executor = None
    time.sleep(3)
    import gc; gc.collect()
    print(
    "RSS final: {}".format(
        convert_size(process.memory_info().rss)
        )
    )

if __name__ == "__main__":
    main()
