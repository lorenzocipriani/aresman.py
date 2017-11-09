#!/usr/bin/env python
'''
aresman.py
@author: Lorenzo Cipriani <lorenzo1974@gmail.com>
@contact: https://www.linkedin.com/in/lorenzocipriani
@since: 2017-10-23
@see:
- P. Mochel, The sysfs Filesystem, 2005

'''

import os
import time

USER_HZ = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
poll_interval = 5

def cpuinfo():
    '''
    '''
    labels = ["processor", "core id", "cpu cores", "model name"]
    cpus = []
    cpu = {}
    processor = None
    
    with open('/proc/cpuinfo') as f:
        for line in f:
            myLine = ' '.join(line.split()).split(':')
            if myLine[0].strip() in labels:
                if myLine[0].strip() == "processor": 
                    processor = myLine[1].strip()
                    cpus.append(None)
                    cpu = {}
                else: cpu[myLine[0].strip()] = myLine[1].strip()
                cpus[int(processor)] = cpu
    return cpus

def toSecs(data):
    '''
    '''
    return float(data)/USER_HZ

def cpustat(data):
    '''
    '''
    cpu = {}
    cpu["id"] = data[0].strip()
    cpu["user"] = data[1].strip()
    cpu["nice"] = data[2].strip()
    cpu["system"] = data[3].strip()
    cpu["idle"] = data[4].strip()
    cpu["iowait"] = data[5].strip()
    cpu["irq"] = data[6].strip()
    cpu["softirq"] = data[7].strip()
    cpu["steal"] = data[8].strip()
    cpu["guest"] = data[9].strip()
    cpu["guest_nice"] = data[10].strip()
    return cpu


def stat():
    '''
    '''
    labels = ["cpu", "btime", "processes", "procs_running", "procs_blocked"]
    cpus = []
    stat = {}
    
    with open('/proc/stat') as f:
        for line in f:
            myLine = line.split(' ')
            if myLine[0].strip() in labels:
                if "cpu" in myLine[0].strip(): cpus.append(cpustat(myLine))
                else: stat[myLine[0].strip()] = myLine[1].strip()
    stat["cpu"] = cpus
    return stat


def main():
    '''
    '''
    try:
        print "Start Time : %s" % time.ctime()
        
        for cpu in cpuinfo():
            print("cpu: {}\tcores: {}\tmodel: {}".format(cpu["core id"], cpu["cpu cores"], cpu["model name"]))
        
        while True:
            
            stats = stat()
            print("uptime: {} sec\tprocs: {} ({} running, {} blocked)".format(toSecs(stats["btime"]), stats["processes"], stats["procs_running"], stats["procs_blocked"]))
            
            for cpu in stats["cpu"]:
                print("id: {}\tuser: {}\tnice: {}\tsystem: {}\tidle: {}\twait: {}".format(cpu["id"], toSecs(cpu["user"], toSecs(cpu["nice"]), toSecs(cpu["system"]), toSecs(cpu["idle"]), toSecs(cpu["iowait"]))))
            
            time.sleep(poll_interval)
        
    except KeyboardInterrupt:
        print("\nAResMan interrupted")
        print "End Time: %s" % time.ctime()


if __name__ == '__main__':
    main()
