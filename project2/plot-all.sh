#!/bin/bash

source outputconfig.py
plotscript="./pubplot.py"

python throughput-plot.py
python drop-plot.py

# Drop rate
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${drop_rate_plot_file} \
       -x "Time (s)" -y "Loss rate (%)" \
       -k "top right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --bmargin 5 --lw 2 \
       --vl 60,180,300,420,540,660,780,900 \
       ${outputs_folder}${tcp_drop_rates_processed} "drop rates" "1:2" \
       | gnuplot

# Drop count
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${drop_count_plot_file} \
       -x "Time (s)" -y "Drops (#pkts)" \
       --yrange "[0:20]" \
       -k "top right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --bmargin 5 --lw 2 \
       --vl 60,180,300,420,540,660,780,900 \
       ${outputs_folder}${tcp_drop_counts_processed} "#dropped pkts" "1:2" \
       | gnuplot

# Link utilization
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${util_plot_file} \
       -x "Time (s)" -y "Link utilization (%)" \
       -k "bottom right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --yrange "[85:105]" \
       --bmargin 5 --lw 2 --lmargin 16 \
       --vl 60,180,300,420,540,660,780,900 \
       ${outputs_folder}${tcp_util_processed} "link utilization" "1:2" \
       | gnuplot

# Send rates
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${src_tput_plot_file} \
       -x "Time (s)" -y "Send rate (Kbit/s)" \
       -k "top right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --bmargin 5 --lw 2 --lmargin 16 \
       --vl 60,180,300,420,540,660,780,900 \
       `cat ${outputs_folder}${src_plot_lines}` \
       | gnuplot

# Receive rates
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${dst_tput_plot_file} \
       -x "Time (s)" -y "Recv rate (Kbit/s)" \
       -k "top right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --bmargin 5 --lw 2 --lmargin 16 \
       --vl 60,180,300,420,540,660,780,900 \
       `cat ${outputs_folder}${dst_plot_lines}` \
       | gnuplot

# Sender cwnd plots
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${cwnd_plot_file} \
       -x "Time (s)" -y "Sender cwnd (pkts)" \
       -k "top right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --bmargin 5 --lw 2 --lmargin 16 \
       --vl 60,180,300,420,540,660,780,900 \
       `cat ${outputs_folder}${cwnd_plot_lines}` \
       | gnuplot

# Sender RTT plots
python $plotscript -a "font \"Times,24\"" \
       -p 1 -f "png" \
       -o ${figs_folder}${rtt_plot_file} \
       -x "Time (s)" -y "Sender sRTT (ms)" \
       -k "top right vertical width 10 spacing 1.5 font \"Times,24\"" \
       --bmargin 5 --lw 2 --lmargin 16 \
       --vl 60,180,300,420,540,660,780,900 \
       `cat ${outputs_folder}${rtt_plot_lines}` \
       | gnuplot

echo "Copying config... all outputs in" $figs_folder
cp config.py $figs_folder/
