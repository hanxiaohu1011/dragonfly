#!/usr/bin/env python3

# imports
import os
import time
import re
import subprocess
import texttable
import argparse

def get_serial_port_received_bytes(host, dport):
    str_cmd = 'ss dst {host} and \( dport = :{dport} \) -i'.format(host=host, dport=dport)
    output = subprocess.Popen(str_cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    p = re.compile(r'bytes_received:(\d+)')

    ret = p.search(output.stdout.read())
    if ret:
        byte_received = ret.group(1)
        return int(byte_received)
    else:
        return 0

def get_serial_info_list(config_path):
    serial_info_list = []
    with open(config_path, 'rb') as f:
        contents = f.read()
        file_as_list = contents.splitlines()  //can be optimized  f.readlines()
        for line in file_as_list:
            each_line = line.split('\t')
            if len(each_line) >= 10:
                host = each_line[1].strip(' \t')
                dport = each_line[2].strip(' \t')
                ttyr = each_line[6].strip(' \t')
                list_info = {'host': host, 'dport': dport, 'ttyr': ttyr}
                serial_info_list.append(list_info)
        return serial_info_list


if __name__ == '__main__':
    #config_path = '/usr/lib/npreal2/driver/npreal2d.cf'
    parser = argparse.ArgumentParser(description='you path')
    parser.add_argument('--path', type = str, default="/usr/lib/npreal2/driver/npreal2d.cf",  help = 'config path')
    parser.add_argument('--time', type = int, default=30, help = 'delay time')
    args = parser.parse_args()
    result_list = list()
    header_list = ['ttyr_name', 'status']
    result_list.append(header_list)
    while True:
        old_bytes_received = 0
        old_bytes_dict = {}
        t = texttable.Texttable()
        t.set_cols_align(["c", "c"])
        #t.set_cols_valign(["t", "t"])
        #t.set_cols_width([11, 11])
        for item  in get_serial_info_list(args.path):
            current_bytes_received = get_serial_port_received_bytes(item['host'], item['dport'])
            single_result = list()
            single_result.append(item['ttyr'])
            old_bytes_received = old_bytes_dict.get('ttyr', 0)
            CBLUE = '\033[94m'
            ENDC = '\033[0m'
            active = CBLUE + '      active' +  ENDC
            status = active if current_bytes_received and (old_bytes_received != current_bytes_received) else 'inactive'
            single_result.append(status)
            # old_bytes_received = current_bytes_received
            old_bytes_dict['ttyr'] = current_bytes_received
            result_list.append(single_result)

        t.add_rows(result_list)
        print t.draw()
        time.sleep(args.time)
