import time
import random
import datetime
import argparse
import numpy as np

from sardana.sardanautils import is_non_str_seq
from sardana.macroserver.recorders.storage import SPEC_FileRecorder
from sardana.macroserver.scan import ColumnDesc
from sardana.macroserver.scan.scandata import RecordList, DataHandler


DESCRIPTION = "Storage Performance Indicator Measurement"


class Scan(object):

    def __init__(self, file_, nb_of_columns=(20, 0, 0), nb_of_points=100,
                 integ_time=.1):
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


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("-f, ", "--file", metavar="file", type=str, nargs="?",
                        required=True, help="File to store the scan data")
    args = parser.parse_args()
    file_ = args.file
        scan = Scan(file_, 
                    nb_of_columns=(20, 0, 1),
                    integ_time=0.001)


if __name__ == "__main__":
    main()
