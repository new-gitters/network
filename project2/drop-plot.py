#!/usr/bin/python

"""
Calculate drop rates from drop counters, and write down loss rates in
number of packets dropped per packet that came in.

Supply an optional argument to indicate at what time granularity the
drop rates should be averaged.

"""

import sys

from config import *
from outputconfig import *

def main(argv=None):
    """ Main """

    averaging_period = -1 # finest granularity available
                          # from data

    stats_file = open(tmp_folder + tcp_stats_file, "r")
    drop_rates_file = open(outputs_folder + tcp_drop_rates_processed, "w")
    drop_counts_file = open(outputs_folder +
                            tcp_drop_counts_processed, "w")
    utils_file = open(outputs_folder + tcp_util_processed, "w")

    prev_dropped = -1
    prev_sent_pkts = -1
    prev_sent_bytes = -1
    prev_overlimits = -1
    prev_sampling_time = -1
    first_line = True

    drop_rates_file.write("# sampling_time(s) drop_percentage(%)\n")
    drop_counts_file.write("# sampling_time(s) drop_counts(#pkts)\n")
    utils_file.write("# sampling_time(s) link_utilization(%)\n")

    for line in stats_file:
        parts = line.strip().split(" ")
        sampling_time = float(parts[0])
        dropped = float(parts[7][:-1]) # [:-1] to remove trailing ','
        overlimits = float(parts[9])
        sent_pkts = float(parts[4])
        sent_bytes = float(parts[2])
        wrote_line = False
            
        if prev_sent_pkts != -1 and sent_pkts != prev_sent_pkts:
            if (averaging_period == -1 or 
                ((averaging_period > 0.0 and 
                  (sampling_time - prev_sampling_time) >
                  averaging_period))):
                drop_rate = ((dropped - prev_dropped) / 
                             ((sent_pkts - prev_sent_pkts) + 
                              (dropped - prev_dropped)) * 100)
                drop_counts = dropped - prev_dropped
                overlimits_rate = ((overlimits - prev_overlimits)
                                   / (sent_pkts - prev_sent_pkts)
                                   * 100.0)
                utilization = (((sent_bytes - prev_sent_bytes) *
                                8.0 * 100.0) /
                               (1000000.0 * (sampling_time -
                                          prev_sampling_time) *
                                bottleneck_bandwidth_Mbps))
                drop_rates_file.write(str(sampling_time) + " " +
                                 str(drop_rate) + "\n")
                drop_counts_file.write(str(sampling_time) + " " +
                                       str(drop_counts) + "\n")
                utils_file.write(str(sampling_time) + " " +
                                 str(utilization) + "\n")
                wrote_line = True

        if first_line or wrote_line:
            prev_dropped = dropped
            prev_sent_pkts = sent_pkts
            prev_sent_bytes = sent_bytes
            prev_overlimits = overlimits
            prev_sampling_time = sampling_time
            first_line = False

    stats_file.close()
    drop_rates_file.close()
    drop_counts_file.close()
    utils_file.close()

if __name__ == "__main__":
    main(sys.argv)
