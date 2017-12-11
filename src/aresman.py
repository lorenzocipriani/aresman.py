#!/usr/bin/env python
'''
aresman.py
@author: Lorenzo Cipriani <lorenzo1974@gmail.com>
@contact: https://www.linkedin.com/in/lorenzocipriani
@since: 2017-10-23
@see:
- P. Mochel, The sysfs Filesystem, 2005

'''

import json
import os
import time
import sys

CUR_UP_1LINE = '\x1b[1A'
ERASE_1LINE = '\x1b[2K'

USER_HZ = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
poll_interval = 5
POLL_HZ = USER_HZ * poll_interval

''' Variables to store the current timestamp and the previous one recorded '''
ts = 000000000
prev_ts = ts
ts_sets = 3 #int((3600/poll_interval)+1)  # number of records stored by timestamp

cpuIds = list()         # cpu cores available on the system
cpuset_queue = ts_sets  # leght of the queue that stores timeseries data for each cpu
''' Structure to hold CPU metrics '''
cpuset = list()
cpu = {
    "ts":"000000000",           # Timestamp (Unix Epoch) when the metrics have been collected
    "user":float(0.0),          # Time spent in user mode
    "nice": float(0.0),         # Time spent in user mode with low priority (nice)
    "system":float(0.0),        # Time spent in system mode
    "idle":float(0.0),          # Time spent in the idle task (USER_HZ times /proc/uptime second entry)
    "iowait":float(0.0),        # Time waiting for I/O to complete (use carefully)
    "irq":float(0.0),           # Time servicing interrupts
    "softirq":float(0.0),       # Time servicing softirqs
    "steal":float(0.0),         # Time spent in other operating systems (when running in a VM)
    "guest":float(0.0),         # Time spent running a virtual CPU for guest operating systems
    "guest_nice":float(0.0),    # Time spent running a niced guest (virtual CPU for guest operating systems)
    "t_user":float(0.0),        # Trend value compared to previos value of user
    "p_user":float(0.0),        # Percentage of time spent for user
    "t_nice": float(0.0),       # Trend value compared to previos value of nice
    "p_nice": float(0.0),       # Percentage of time spent for nice
    "t_system":float(0.0),      # Trend value compared to previos value of system
    "p_system":float(0.0),      # Percentage of time spent for system
    "t_idle":float(0.0),        # Trend value compared to previos value of idle
    "p_idle":float(0.0),        # Percentage of time spent for idle
    "t_iowait":float(0.0),      # Trend value compared to previos value of iowait
    "p_iowait":float(0.0),      # Percentage of time spent for iowait
    "t_irq":float(0.0),         # Trend value compared to previos value of irq
    "p_irq":float(0.0),         # Percentage of time spent for irq
    "t_softirq":float(0.0),     # Trend value compared to previos value of softirq
    "p_softirq":float(0.0),     # Percentage of time spent for softirq
    "t_steal":float(0.0),       # Trend value compared to previos value of steal
    "p_steal":float(0.0),       # Percentage of time spent for steal
    "t_guest":float(0.0),       # Trend value compared to previos value of guest
    "p_guest":float(0.0),       # Percentage of time spent for guest
    "t_guest_nice":float(0.0),  # Trend value compared to previos value of guest_nice
    "p_guest_nice":float(0.0)   # Percentage of time spent for guest_nice
}

''' Structure to hold Memory metrics '''
memset = list()
mem = {
    "ts":"000000000",         # Timestamp (Unix Epoch) when the metrics have been collected
    "MemTotal":int(0),        # Total usable RAM
    "MemFree":int(0),         # The sum of LowFree + HighFree
    "MemAvailable":int(0),    # Memory available for starting new applications, without swapping (estimate)
    "SwapTotal":int(0),       # Total amount of swap space available
    "SwapFree":int(0),        # Amount of swap space that is currently unused
    "p_MemFree":int(0),       # Percentage of MemFree
    "p_MemAvailable":int(0),  # Percentage of MemAvailable
    "p_SwapFree":int(0)       # Percentage of SwapFree
}

''' Structure to hold Process metrics '''
procset = list()
proc = {
    "ts":"000000000",         # Timestamp (Unix Epoch) when the metrics have been collected
    "cmdline":"                                                            ",
    "state":" ",              # Process state (see man 5 proc)
    "vsize":int(0),           # Virtual memory size in bytes
    "rss":int(0)             # Resident Set Size: number of pages the process has in real memory
}


def toSecs(data):
    '''
    '''
    if data is None or data == "": data = 0
    return float( int(data) / int(USER_HZ) )


def reserveMemory():
    '''
    To grant that the running programm will always have a memory block already
    allocated.
    The size is evaluated on a vector of mestrics collected multiplied for the 
    number of records that will be kept in memory for an hour (3600 secs)
    '''
    global ts_sets
    global cpuIds, cpuset, cpu
    global memset, mem

    ''' Read all the cores in the system and prepare the cpuIds list '''    
    cpuIds.append("cpu")
    for cpus in cpuinfo(): cpuIds.append("cpu" + str(cpus["core id"]))

    ''' For each core prepare a structure to host data '''
    for id in cpuIds: cpuset.append({id:[cpu]*ts_sets})
    
    ''' Prepare a structure to host memory data '''
    memset.append([mem]*ts_sets)
    
    #print("reserveMemory()", cpuIds)
    #print("reserveMemory()", cpuset)


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
    

def cpuTrend(cpuStat, prev, tf):
    '''
    Calculate the difference between the current cpu stat and the previous one
    '''

    ''' If previous values are 0 then init to 1.0 the trend value and 0.0 the percentage one '''
    try:
        if float(prev["user"]) == 0:
            t_user = 1.0
            p_user = 0.0
        else: 
            t_user = 1/(float(cpuStat["user"])/float(prev["user"]))
            p_user = 0.0
            d_user = (float(cpuStat["user"])-float(prev["user"]))
            if d_user != 0: p_user = 1/(tf/d_user)
    except ValueError:
        t_user = prev["user"]
        p_user = prev["p_user"]
    try:
        if float(prev["nice"]) == 0: 
            t_nice = 1.0
            p_nice = 0.0
        else: 
            t_nice = 1/(float(cpuStat["nice"])/float(prev["nice"]))
            p_nice = 0.0
            d_nice = (float(cpuStat["nice"])-float(prev["nice"]))
            if d_nice != 0: p_nice = 1/(tf/d_nice)
    except ValueError:
        t_nice = prev["nice"]
        p_nice = prev["p_nice"]
    try:
        if float(prev["system"]) == 0: 
            t_system = 1.0
            p_system = 0.0
        else: 
            t_system = 1/(float(cpuStat["system"])/float(prev["system"]))
            p_system = 0.0
            d_system = (float(cpuStat["system"])-float(prev["system"]))
            if d_system != 0: p_system = 1/(tf/d_system)
    except ValueError:
        t_system = prev["system"]
        p_system = prev["p_system"]
    try:
        if float(prev["idle"]) == 0: 
            t_idle = 1.0
            p_idle = 0.0
        else: 
            t_idle = 1/(float(cpuStat["idle"])/float(prev["idle"]))
            p_idle = 0.0
            d_idle = (float(cpuStat["idle"])-float(prev["idle"]))
            if d_idle != 0: p_idle = 1/(tf/d_idle)
    except ValueError:
        t_idle = prev["idle"]
        p_idle = prev["p_idle"]
    try:
        if float(prev["iowait"]) == 0: 
            t_iowait = 1.0
            p_iowait = 0.0
        else: 
            t_iowait = 1/(float(cpuStat["iowait"])/float(prev["iowait"]))
            p_iowait = 0.0
            d_iowait = (float(cpuStat["iowait"])-float(prev["iowait"]))
            if d_iowait != 0: p_iowait = 1/(tf/d_iowait)
    except ValueError:
        t_iowait = prev["iowait"]
        p_iowait = prev["p_iowait"]
    try:
        if float(prev["irq"]) == 0: 
            t_irq = 1.0
            p_irq = 0.0
        else: 
            t_irq = 1/(float(cpuStat["irq"])/float(prev["irq"]))
            p_irq = 0.0
            d_irq = (float(cpuStat["irq"])-float(prev["irq"]))
            if d_irq != 0: p_irq = 1/(tf/d_irq)
    except ValueError:
        t_irq = prev["irq"]
        p_irq = prev["p_irq"]
    try:
        if float(prev["softirq"]) == 0: 
            t_softirq = 1.0
            p_softirq = 0.0
        else: 
            t_softirq = 1/(float(cpuStat["softirq"])/float(prev["softirq"]))
            p_softirq = 0.0
            d_softirq = (float(cpuStat["softirq"])-float(prev["softirq"]))
            if d_softirq != 0: p_softirq = 1/(tf/d_softirq)
    except ValueError:
        t_softirq = prev["softirq"]
        p_softirq = prev["p_softirq"]
    try:
        if float(prev["steal"]) == 0: 
            t_steal = 1.0
            p_steal = 0.0
        else: 
            t_steal = 1/(float(cpuStat["steal"])/float(prev["steal"]))
            p_steal = 0.0
            d_steal = (float(cpuStat["steal"])-float(prev["steal"]))
            if d_steal != 0: p_steal = 1/(tf/d_steal)
    except ValueError:
        t_steal = prev["steal"]
        p_steal = prev["p_steal"]
    try:
        if float(prev["guest"]) == 0: 
            t_guest = 1.0
            p_guest = 0.0
        else: 
            t_guest = 1/(float(cpuStat["guest"])/float(prev["guest"]))
            p_guest = 0.0
            d_guest = (float(cpuStat["guest"])-float(prev["guest"]))
            if d_guest != 0: p_guest = 1/(tf/d_guest)
    except ValueError:
        t_guest = prev["guest"]
        p_guest = prev["p_guest"]
    try:
        if float(prev["guest_nice"]) == 0: 
            t_guest_nice = 1.0
            p_guest_nice = 0.0
        else: 
            t_guest_nice = 1/(float(cpuStat["guest_nice"])/float(prev["guest_nice"]))
            p_guest_nice = 0.0
            d_guest_nice = (float(cpuStat["guest_nice"])-float(prev["guest_nice"]))
            if d_guest_nice != 0: p_guest_nice = 1/(tf/d_guest_nice)
    except ValueError:
        t_guest_nice = prev["guest_nice"]
        p_guest_nice = prev["p_guest_nice"]
    
    cpuStat = {
        "ts":cpuStat["ts"],
        "user":cpuStat["user"],
        "nice": cpuStat["nice"],
        "system":cpuStat["system"],
        "idle":cpuStat["idle"],
        "iowait":cpuStat["iowait"],
        "irq":cpuStat["irq"],
        "softirq":cpuStat["softirq"],
        "steal":cpuStat["steal"],
        "guest":cpuStat["guest"],
        "guest_nice":cpuStat["guest_nice"],
        "t_user":t_user,
        "p_user":p_user,
        "t_nice":t_nice,
        "p_nice":p_nice,
        "t_system":t_system,
        "p_system":p_system,
        "t_idle":t_idle,
        "p_idle":p_idle,
        "t_iowait":t_iowait,
        "p_iowait":p_iowait,
        "t_irq":t_irq,
        "p_irq":p_irq,
        "t_softirq":t_softirq,
        "p_softirq":p_softirq,
        "t_steal":t_steal,
        "p_steal":p_steal,
        "t_guest":t_guest,
        "p_guest":p_guest,
        "t_guest_nice":t_guest_nice,
        "p_guest_nice":p_guest_nice
    }
    #print("cpuTrend()", cpuStat)
    return cpuStat
    

def cpusetAdd(cpuId, cpuStat):
    '''
    Append a cpu stat vector to the cpuset list and calculate the trend compared
    to the previous timestamp
    '''
    global cpuIds, cpuset, ts_sets
    global POLL_HZ
    
    tf = POLL_HZ
    if cpuId == "cpu": tf *= len(cpuIds) - 1

    idx = -1
    for cpuDict in cpuset:
        idx += 1
        if cpuDict.has_key(cpuId):
            cpuDict[cpuId].insert(0, cpuTrend(cpuStat, cpuDict[cpuId][0], tf))
            #print("cpuDict", cpuId, cpuDict[cpuId])
            ''' If the queue is full, remove the oldest record '''
            if len(cpuDict[cpuId]) > ts_sets: del cpuDict[cpuId][-1]
            cpuset[idx] = {cpuId:cpuDict[cpuId]}
            #print("cpuset", idx, cpuset[idx])
            break
    
    #print("cpusetAdd", cpuset[idx])
    #print("\ncpuset\n", cpuset)
        
    
def cpustat(data):
    '''
    Parse cpu stats from the /proc/stat output and assign values to global cpu
    
    Values are converted to float(0.0) in case the original value is not a 
    convertible number
    '''
    global ts, cpu
    
    cpuId = data[0].strip()

    try: user = float(data[1].strip())
    except ValueError: user = float(0.0)
    try: nice = float(data[2].strip())
    except ValueError: nice = float(0.0)
    try: system = float(data[3].strip())
    except ValueError: system = float(0.0)
    try: idle = float(data[4].strip())
    except ValueError: idle = float(0.0)
    try: iowait = float(data[5].strip())
    except ValueError: iowait = float(0.0)
    try: irq = float(data[6].strip())
    except ValueError: irq = float(0.0)
    try: softirq = float(data[7].strip())
    except ValueError: softirq = float(0.0)
    try: steal = float(data[8].strip())
    except ValueError: steal = float(0.0)
    try: guest = float(data[9].strip())
    except ValueError: guest = float(0.0)
    try: guest_nice = float(data[10].strip())
    except ValueError: guest_nice = float(0.0)

    cpu = {
        "ts":ts,
        "user":user,
        "nice":nice,
        "system":system,
        "idle":idle,
        "iowait":iowait,
        "irq":irq,
        "softirq":softirq,
        "steal":steal,
        "guest":guest,
        "guest_nice":guest_nice,
        "t_user":float(0.0),
        "p_user":float(0.0),
        "t_nice": float(0.0),
        "p_nice": float(0.0),
        "t_system":float(0.0),
        "p_system":float(0.0),
        "t_idle":float(0.0),
        "p_idle":float(0.0),
        "t_iowait":float(0.0),
        "p_iowait":float(0.0),
        "t_irq":float(0.0),
        "p_irq":float(0.0),
        "t_softirq":float(0.0),
        "p_softirq":float(0.0),
        "t_steal":float(0.0),
        "p_steal":float(0.0),
        "t_guest":float(0.0),
        "p_guest":float(0.0),
        "t_guest_nice":float(0.0),
        "p_guest_nice":float(0.0)
    }
    #print("cpustat()", cpuId, cpu)
    return cpuId, cpu


def stat():
    '''
        Collects the metrics from /proc/stat
    '''
    global ts, prev_ts
    global poll_interval
    global cpuset, cpu

    labels = ["btime", "uptime", "processes", "procs_running", "procs_blocked"]
    cpus = []
    stat = {}
    
    with open('/proc/stat') as f:
        for line in f:
            myLine = line.split(' ')
            if "cpu" in myLine[0].strip():
                cpuId, cpuStat = cpustat(myLine)
                cpusetAdd(cpuId, cpuStat)
            elif myLine[0].strip() in labels: stat[myLine[0].strip()] = myLine[1].strip()
    stat["uptime"] = time.time() - float(stat["btime"])

    ''' Store cpus stat in the time series set '''
    for cpuId in cpus: cpuset = {ts:cpuId}
    
    return stat


def meminfo():
    '''
    '''
    labels = ["MemTotal", "MemFree", "MemAvailable", "SwapTotal", "SwapFree"]
    mem = {}
    
    with open('/proc/meminfo') as f:
        for line in f:
            myLine = line.split(':')
            if myLine[0].strip() in labels: mem[myLine[0].strip()] = myLine[1].strip()
    return mem

def main():
    '''
    '''
    try:
        global ts, prev_ts
        global poll_interval
        global cpuIds, cpuset, cpu

        print "Start Time : %s" % time.ctime()
        
        for cpus in cpuinfo():
            print("cpu: {}\tcores: {}\tmodel: {}".format(cpus["core id"], cpus["cpu cores"], cpus["model name"]))
        
        while True:
            ''' Save the previous timestamp and calculate the current one '''
            prev_ts = ts
            ts = int(time.time())
            
            stats = stat()
            print("uptime: {} sec\tprocs: {} ({} running, {} blocked)".format(stats["uptime"], stats["processes"], stats["procs_running"], stats["procs_blocked"]))
            
            mem = meminfo()
            print("Memory: Total {}  Free {}  Available {}".format(mem["MemTotal"], mem["MemFree"], mem["MemAvailable"]))
            print("Swap: Total {}  Free {}".format(mem["SwapTotal"], mem["SwapFree"]))

            for cpuDict in cpuset:
                for cpuKey, cpuVal in cpuDict.iteritems():
                    print("{}\tuser: {} [{}]  nice: {} [{}]  system: {} [{}]  idle: {} [{}]  wait: {} [{}]".format(
                        cpuKey, 
                        "{0:.2f}".format((cpuVal[0]["p_user"]*100)), "{0:.2f}".format(cpuVal[1]["p_user"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_nice"]*100)), "{0:.2f}".format(cpuVal[1]["p_nice"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_system"]*100)), "{0:.2f}".format(cpuVal[1]["p_system"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_idle"]*100)), "{0:.2f}".format(cpuVal[1]["p_idle"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_iowait"]*100)), "{0:.2f}".format(cpuVal[1]["p_iowait"]*100)
                        )
                )
            
            time.sleep(poll_interval)

            sys.stdout.write((3 + len(cpuIds)) * (CUR_UP_1LINE + ERASE_1LINE))
            sys.stdout.flush()

            #print json.dumps(cpuset)
        
    except KeyboardInterrupt:
        print("\nAResMan interrupted")
        print "End Time: %s" % time.ctime()


if __name__ == '__main__':
    
    print "Start aresman with pid[" + str(os.getpid()) + "]"
    
    ''' Increase process priority at a higher level, close to the kernel one '''
    os.nice(-15)
    
    ''' Preallocate memory space for system metric collection '''
    reserveMemory()
    
    ''' Start the agent '''
    main()
