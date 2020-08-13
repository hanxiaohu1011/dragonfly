#!/usr/bin/python3

import time
import datetime
import json
import telnetlib
import unittest
import os
import logging
import logging.handlers
from datetime import datetime, timedelta

def remote(cmd, ip="10.62.60.191", port=2000):
    print("\nroot@Agent:~$ run_cmd: {} {}".format(cmd['cmd'], cmd.get("name", "")))
    tn = telnetlib.Telnet(ip, port)
    cmdline = json.dumps(cmd) + "\n"
    tn.write(cmdline.encode("iso-8859-1"))
    try:
        while True:
            result = tn.read_until(b'\n').decode("iso-8859-1")
            try:
                s = json.loads(result)
                print(json.dumps(s, indent=4))
            except Exception:
                print(result.rstrip())
    except EOFError:
        pass
    tn.close()
    print("\nroot@Agent:~$ ")

def get_logger(name):
    logger = logging.getLogger(name)
    handler = logging.handlers.RotatingFileHandler("robust.log", maxBytes=1024*1024)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
class SequenceTest(unittest.TestCase):

    def test_get_status(self):
        remote({"cmd": "fake_command"})
        remote({"cmd": "status"})
        remote({"cmd": "get_ip", 'mac': "00:60:16:fB:63:05"})

    def test_0_set_dhcp(self):
        cmd = {"cmd": "list_dhcp"}
        remote(cmd)
        print("root@Agent:~$ # Will setup pxe booting parameters. Press enter to continue")
        cmd = {"cmd": "set_dhcp",
               'mac': "00:60:16:fB:63:05",
               "ip": "192.168.88.160",
               "subnet": "255.255.255.0",
               "router": "192.168.88.1",
               "os": "ubuntu18.04.1"}
        remote(cmd)

        cmd = {"cmd": "list_dhcp"}
        remote(cmd)
        cmd = {"cmd": "test_set_lease", "mac": "00:60:16:fB:63:ff", "ip": "192.168.88.91"}
        remote(cmd)
        cmd = {"cmd": "test_set_lease", "mac": "00:60:16:fB:63:f3", "ip": "192.168.88.1"}
        remote(cmd) 

    def test_1_reboot_uut(self):
        print("root@Agent:~$ # Will reboot uut. Press enter to continue")
        cmd = {
            "cmd": "exec",
            "name": "ipmitool",
            "version": "1.8.16",
            "operation": "power_cycle",
            "args": ["ip={mac(00:60:16:fB:63:ff)}"],
            "timeout": 200,
            "local": True}
        remote(cmd)

    def test_2_wait_uut_up(self):
        cmd = {"cmd": "wait_up", "target_mac": "00:60:16:fB:63:05", "timeout": 200}
        remote(cmd)

    def test_3_install_tool(self):
        print("root@Agent:~$ # Will install iperf3. Press enter to continue")
        cmd = {"cmd": "install_tool", "name": "iperf3", "version": "3.1.3", "os": "ubuntu18.04.1", "target_mac": "00:60:16:fB:63:05"}
        remote(cmd)

    def test_4_exec_cmd(self):
        print("root@Agent:~$ # Will execute bandwidth test. Press enter to continue")
        cmd = {"cmd": "exec", "name": "iperf3", "args": ["-c", "192.168.88.1"], "target_mac": "00:60:16:fB:63:05"}
        remote(cmd)

    def test_5_test_set_lease_ip(self):
        cmd = {"cmd": "test_set_lease", "mac": "00:60:16:fB:63:05", "ip": "192.168.88.160"}
        remote(cmd)

if __name__ == '__main__':
    test = SequenceTest()
    nexttime = datetime.now() + timedelta(hours=3)
    delay = (nexttime - datetime.now()).total_seconds()
    logger = get_logger("robust")
    frequency = 1
    while True:
        try:
            test.test_0_set_dhcp()
            test.test_1_reboot_uut()
            test.test_5_test_set_lease_ip()
            test.test_2_wait_uut_up()
            test.test_3_install_tool()
            test.test_4_exec_cmd()
        except OSError as e:
            logger.error('service occurs error')
            quit()
        logger.info('testcases already execute {} times'.format(frequency))
        time.sleep(delay)
        frequency += 1 
        
