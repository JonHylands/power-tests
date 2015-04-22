#!/usr/bin/env python
#

import os
from optparse import OptionParser
from urlparse import urlparse
import time

#("name: power.%s.current\n" % powerProfile["testName"])
#("time: %s\n" % powerProfile["epoch"])
#("value: %s\n" % powerProfile["average"])
#("context: %s\n" % powerProfile["context"])


class RaptorTestPoster(object):

#   "name": "flash.idle_screen_on.current",
#"columns": ["time", "entryType", "context", "appName", "epoch", "value", "branch", "device", "memory"],
# "points": [[1400425947368, "current", "verticalhome.gaiamobile.org", "Homescreen", 1429214460095, 350, "master", "flame-kk", 1024]]

    def post_to_raptor(self, results):

        #json_string = '[{"name": "flash.idle_screen_on.current","columns": ["time", "entryType", "context", "appName", "epoch", "value", "branch", "device", "memory"],"points": [[1400425947368, "current", "verticalhome.gaiamobile.org", "Homescreen", 1429214460095, 350, "master", "flame-kk", 1024]]}]'
        json_string = '[{"name": "'
        json_string += results["name"]
        json_string += '", "columns": ["time", "entryType", "context", "appName", "epoch", "value", "branch", "device", "memory"], '
        json_string += '"points": [['
        json_string += str(results["time"])
        json_string += ', "current", "'
        json_string += results["context"]
        json_string += '", "'
        json_string += results["app_name"]
        json_string += '", '
        json_string += str(results["time"])
        json_string += ', '
        json_string += str(results["value"])
        json_string += ', "master", "flame-kk", 1024]]}]'

        command_string = """\
curl -X POST -d '%(json)s' \
'http://goldiewilson-onepointtwentyone-1.c.influxdb.com:8086/db/raptor/series?u=power&p=123456'""" % {'json': json_string}

        print "os.system - ", command_string
        os.system(command_string)


class raptorOptionParser(OptionParser):
    def __init__(self, **kwargs):
        OptionParser.__init__(self, **kwargs)
        self.add_option('--file',
                        action='store',
                        dest='results_file',
                        metavar='str',
                        help='Json checkpoint results file from the power test')
        self.add_option('--process-dir',
                        action='store',
                        dest='process_dir',
                        metavar='str',
                        help='Process all *_summary.log files in the given folder')

    #def raptor_config(self, options):
        #if options.sources:
            #if not os.path.exists(options.sources):
                #raise Exception('--sources file does not exist')

        #datazilla_url = urlparse(options.datazilla_url)
        #datazilla_config = {
            #'protocol': datazilla_url.scheme,
            #'host': datazilla_url.hostname,
            #'project': options.datazilla_project,
            #'branch': options.datazilla_branch,
            #'device_name': options.datazilla_device_name,
            #'oauth_key': options.datazilla_key,
            #'oauth_secret': options.datazilla_secret}
        #return datazilla_config


def cli():
    parser = raptorOptionParser(usage='%prog file [options]')
    options, args = parser.parse_args()

    # Either a single file or option to process all in given folder
    if (not options.results_file) and (not options.process_dir):
        parser.print_help()
        parser.exit()

    if options.results_file and options.process_dir:
        parser.print_help()
        parser.exit()

    # Ensure results file actually exists
    if options.results_file:
        if not os.path.exists(options.results_file):
            raise Exception('%s file does not exist' %options.results_file)
        
    if options.process_dir:
        if not os.path.exists(options.process_dir):
            raise Exception("Process all path '%s' does not exist" %options.process_dir) 

    # Parse config options
    # raptor_config = parser.raptor_config(options)

   # Parse results from provided summary log file
    results = {}
    summary_file_list = []

    if options.process_dir:
        # All files in the given path
        file_path = options.process_dir
        print "\nSearching for *_summary.log files in %s\n" % options.process_dir

        entire_file_list = os.listdir(file_path)

        if len(entire_file_list) == 0:
            raise Exception("No checkpoint *_summary.log files were found in the given path")
        for found_file in entire_file_list:
            if found_file.endswith("summary.log"):
                summary_file_list.append("%s/%s" % (file_path, found_file))
        if len(summary_file_list) == 0:
            raise Exception("No checkpoint *_summary.log files were found in the given path")

        print "Found the following checkpoint summary files to process:\n"
        for x in summary_file_list:
            print "%s" % x
        print "\n" + "-" * 50         
    else:
        # Just one file
        summary_file_list = [options.results_file]

    for next_file in summary_file_list:

        # Clear results as only want results for current file being processed
        results = {}

        print "\nProcessing results in '%s'\n" % next_file

        summary_file = open(next_file, 'r')
        read_in = summary_file.read().split("\n")
        summary_file.close()

        for x in read_in:
            if x.find(':') != -1: # Ignore empty lines ie. last line of file which is empty
                k, v = x.split(': ')
                if k in ["average", "test_runtime", "completed"]:
                    results[k] = int(v)
                else:
                    results[k] = v

        # Create raptor post object
        poster = RaptorTestPoster()
        poster.post_to_raptor(results)


    if options.process_dir:
        print "\nFinished processing all files.\n"

if __name__ == '__main__':
    cli()
