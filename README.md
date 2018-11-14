This project contains scripts foreseen for measuring the Alba storage system
performance. The results will be used for composing the performance 
indicators.

# Dependencies for script sardana_scan

- lxml
- taurus
- sardana (without its dependencies)

It can be easily installed in a virtualenv with the following commands

~~~
# create virtual env directory
$> mkdir sardana-kpi-ve
# create virtual env
$> virtualenv sardana-kpi-ve
# activate virtual env
$> source sardana-kpi-ve/bin/activate
# install lxml and taurus
$> pip install lxml taurus
# install sardana from zreszela's fork (soon it will be available in the official repo)
$> pip install --no-deps git+https://github.com/reszelaz/sardana.git@storage-tango-indep
# to deactive the virtual env run: deactivate
~~~

# Usage of script sardana_scan

By default the script sardana_scan.py will execute a single step scan of 100 
 points and 0.1 second of the integration time with 20 measurement channels. 
 One needs to specify where to create the data file with the `--file` option. 
 The data will be automatically appended to the existing file.
 
~~~
$> python sardana_scan.py --file=/tmp/storage.dat
~~~
 


# Script txm_emulator and its usage

Emulator of image creation. Images of 1024*1024 are stored as
 hdf5 files. This emulates the BL09 image acquistion process
 (but in hdf5 instead than in xrm).
    
 Usage:
 
 ~~~
 $> python txm_emulator.py -n 5 -s 0.5
 ~~~
 
 -n: number of images to be stored
 -s: sleep time between stored images)
