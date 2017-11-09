#!/usr/bin/env python
'''
aresman.py
@author: Lorenzo Cipriani <lorenzo1974@gmail.com>
@contact: https://www.linkedin.com/in/lorenzocipriani
@since: 2017-10-23
@see:
- P. Mochel, The sysfs Filesystem, 2005

'''

import time

poll_interval = 10

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
                    cpus.append(cpu)
                else: cpu[myLine[0].strip()] = myLine[1].strip()
                cpus[int(processor)] = cpu

        print(cpus)


def main():
    '''
    '''
    try:
        print "Start Time : %s" % time.ctime()
        while True:
            
            cpuinfo()
            
            time.sleep(poll_interval)
        
    except KeyboardInterrupt:
        print("\nAResMan interrupted")
        print "End Time: %s" % time.ctime()


if __name__ == '__main__':
    main()
