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
    with open('/proc/cpuinfo') as f:
        for line in f:
            print(line.rstrip('\n'))


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
