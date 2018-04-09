This project contains scripts foreseen for measuring the Alba storage system
performance. The results will be used for composing the performance 
indicators.

# Dependencies

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

# Usage

By default this script will execute a single step scan of 100 points and 0.1
 second of the integration time with 20 measurement channels. One needs to 
 specify where to create the data file with the `--file` option. The data will
 be automatically appended to the existing file.
 
~~~
$> python sardana_scan.py --file=/tmp/storage.dat
~~~
 

