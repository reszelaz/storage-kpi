import h5py
import time
import numpy as np
import argparse


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


class TXMEmulator(object):
    """Emulate BL09 image collection"""

    def emulate(self, num_imgs, sleep_between_images):
        base_name = "img_"
        data_set = "data"
        for i in range(num_imgs):
            image = np.random.randint(0, 65536, size=(1024, 1024))
            h5_filename = base_name + str(i) + ".hdf5"
            f = h5py.File(h5_filename, 'w')
            f.create_dataset(data_set, data=image, dtype=np.uint16)
            #f.flush()
            f.close()
            time.sleep(sleep_between_images)
            print(h5_filename)

def main():

    parser = argparse.ArgumentParser(description="TXM image acquisition "
                                                 "(collect) emulation",
                                     formatter_class=CustomFormatter)

    parser.add_argument('-n', '--num_imgs', type=int, default=1,
                        help='Num images to be written (-s=1).')
    parser.add_argument('-s', '--sleep', type=float, default=1,
                        help='Sleep time between image collection')

    args = parser.parse_args()

    print("beginning")
    emultator_obj = TXMEmulator()
    a=time.time()
    emultator_obj.emulate(args.num_imgs, args.sleep)
    b = time.time()
    c = b - a
    print("ellapsed time %f" % c)

if __name__ == "__main__":
    main()





