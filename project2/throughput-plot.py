#!/usr/bin/python

"""
Construct the iperf time, throughput from TCP and UDP traces, and put
them into their "processed" files.
"""

import sys
import subprocess

from config import *
from outputconfig import *

src_tput_line = ""
dst_tput_line = ""
cwnd_line = ""
rtt_line = ""
src_prefix = "hsrc"
dst_prefix = "hdst"

def extract_tput(file_input, file_output):
    """ construct commands and extract output from data processing """
    header_cmd = ("echo '# sampling_time(s) measured_throughput(Kbit/s)' > " +
                  file_output)
    tput_cmd = ("tail --lines=+7 " + file_input + " | awk "
                "-F- '{print $2}' | awk '$6 == \"Kbits/sec\" {print $1"
                "\" \" $5} $6 == \"Mbits/sec\" {print $1 \" \""
                "$5*1000} $6 == \"bits/sec\" {print $1 \" \" "
                "$5/1000.0}' >> " + file_output)

    # diagnostic
    if debug_mode:
        print header_cmd
        print tput_cmd

    # run commands in shell
    out1 = subprocess.check_output(header_cmd, shell=True)
    out2 = subprocess.check_output(tput_cmd, shell=True)

def extract_cwnd_rtt(flow_index, file_output):
    header_cmd = ("echo '# sampling_time(s) snd_cwnd(#pkts) sRTT(ms)'" +
                  " > " + file_output)
    cwnd_rtt_cmd = ("awk -F':' 'substr($3, 0, 4) == 500 {print}' " +
                    tmp_folder + tcp_probe_file +
                    " | awk 'substr($3, 0, " +
                    str(8 + len(str(flow_index))) +
                    ") == \"10.0.0." +  str(flow_index) +
                    "\" {print $1 \" \" $7 \" \" $10 }' > " +
                    file_output)
    if debug_mode:
        print header_cmd
        print cwnd_rtt_cmd

    subprocess.check_output(header_cmd, shell=True)
    subprocess.check_output(cwnd_rtt_cmd, shell=True)

def processHost(src_dst_prefix, hostpair_index):
    """ Process a single host -- source or destination """
    iperf_input_file = (tmp_folder +
                        src_dst_prefix +
                        str(hostpair_index) + 
                        tcp_server_throughput_suffix)
    iperf_output_file = (outputs_folder +
                         src_dst_prefix +
                         str(hostpair_index) +
                         tcp_processed_suffix)                            
    extract_tput(iperf_input_file, iperf_output_file)

def processSrcCwndRtt(hostpair_index):
    cwnd_rtt_output_file = (outputs_folder +
                            src_prefix +
                            str(hostpair_index) +
                            cwnd_rtt_suffix)
    extract_cwnd_rtt(hostpair_index + 1, cwnd_rtt_output_file)
    addRttPlotline(hostpair_index, cwnd_rtt_output_file)
    addCwndPlotline(hostpair_index, cwnd_rtt_output_file)

def addCwndPlotline(hostpair_index, output_file):
    global cwnd_line
    cwnd_line += (output_file +
                  " cwnd-" +
                  str(hostpair_index) +
                  " ($1-2):2 ")

def addRttPlotline(hostpair_index, output_file):
    global rtt_line
    rtt_line += (output_file +
                 " rtt-" +
                 str(hostpair_index) +
                 " ($1-2):($3/1000) " )
    
def addSrcPlotline(hostpair_index):
    global src_tput_line
    src_tput_line += (outputs_folder +
                      src_prefix +
                      str(hostpair_index) +
                      tcp_processed_suffix +
                      " src-" +
                      str(hostpair_index) +
                      " 1:2 ")

def addDstPlotline(hostpair_index):
    global dst_tput_line
    dst_tput_line += (outputs_folder +
                      dst_prefix +
                      str(hostpair_index) +
                      tcp_processed_suffix +
                      " dst-" +
                      str(hostpair_index) +
                      " 1:2 ")

def printPlotlines():
    f = open(outputs_folder + src_plot_lines, "w")
    f.write(src_tput_line)
    f.close()
    f = open(outputs_folder + dst_plot_lines, "w")
    f.write(dst_tput_line)
    f.close()
    f = open(outputs_folder + rtt_plot_lines, "w")
    f.write(rtt_line)
    f.close()
    f = open(outputs_folder + cwnd_plot_lines, "w")
    f.write(cwnd_line)
    f.close()
    
def main(argv=None):
    """ Main """
    for i in range(0, num_hostpairs):
        processHost(dst_prefix, i)
        processHost(src_prefix, i)
        addSrcPlotline(i)
        addDstPlotline(i)
        processSrcCwndRtt(i)
    printPlotlines()
        
if __name__ == "__main__":
    main()
