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
import signal
import sys
from _cffi_backend import string

CUR_UP_1LINE = '\x1b[1A'
ERASE_1LINE = '\x1b[2K'

USER_HZ = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
poll_interval = 5
POLL_HZ = USER_HZ * poll_interval

KILL_AFTER = int(2)
pid_kill_counter = {"0": int(0)}

CPU_LIMIT = float(85.0)
cpu_usage = float(0.0)

''' Variables to store the current timestamp and the previous one recorded '''
ts = 000000000
prev_ts = ts
ts_sets = 3 #int((3600/poll_interval)+1)  # number of records stored by timestamp

cpuIds = list()         # cpu cores available on the system
#cpuset_queue = ts_sets  # leght of the queue that stores timeseries data for each cpu

''' Structure to hold CPU metrics '''
cpuset = list()
cpu = {
    "ts":"000000000",           # Timestamp (Unix Epoch) when the metrics have been collected
    "user":float(0.0),          # Time spent in user mode
    "nice": float(0.0),         # Time spent in user mode with low priority (nice)
    "system":float(0.0),        # Time spent in system mode
    "idle":float(0.0),          # Time spent in the idle task (USER_HZ times /proc/uptime second entry)
    "iowait":float(0.0),        # Time waiting for I/O to complete (use carefully)
    "rss":float(0.0),           # Time servicing interrupts
    "softrss":float(0.0),       # Time servicing softrsss
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
    "t_rss":float(0.0),         # Trend value compared to previos value of rss
    "p_rss":float(0.0),         # Percentage of time spent for rss
    "t_softrss":float(0.0),     # Trend value compared to previos value of softrss
    "p_softrss":float(0.0),     # Percentage of time spent for softrss
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

procIds = list()              # processes running on the system
''' Structure to hold Process metrics '''
procset = list()
proc = {
    "ts":"000000000",        # Timestamp (Unix Epoch) when the metrics have been collected
    "cmdline":"                                                           ",
    "pid":int(0),              #  1 The process ID
    "state":" ",               #  3 Process state (see man 5 proc)
    "ppid":int(0),             #  4 The PID of the parent of this process
    "utime":float(0.0),        # 14 Amount of time scheduled in user mode
    "stime":float(0.0),        # 15 Amount of time scheduled in kernel mode
    "cutime":float(0.0),       # 16 Amount of time waited-for children scheduled in user mode 
    "cstime":float(0.0),       # 17 Amount of time waited-for children scheduled in kernel mode 
    "starttime":float(0.0),    # 22 The time the process started after system boot 
    "vsize":int(0),            # 23 Virtual memory size in bytes
    "rss":int(0),              # 24 Resident Set Size: number of pages the process has in real memory
    "p_utime":float(0.0),      # Percentage of time scheduled in user mode                      
    "p_stime":float(0.0),      # Percentage of time scheduled in kernel mode                    
    "p_cutime":float(0.0),     # Percentage of time waited-for children scheduled in user mode  
    "p_cstime":float(0.0),     # Percentage of time waited-for children scheduled in kernel mode
    "p_vsize":float(0.0),      # Percentage of virtual memory
    "p_rss":float(0.0)         # Percentage of the number of pages in real memory
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
    global procset, proc

    ''' Read all the cores in the system and prepare the cpuIds list '''    
    cpuIds.append("cpu")
    for cpus in cpuinfo(): cpuIds.append("cpu" + str(cpus["core id"]))

    ''' For each core prepare a structure to host data '''
    for id in cpuIds: cpuset.append({id:[cpu]*ts_sets})
    
    ''' Prepare a structure to host memory data '''
    memset.append([mem]*ts_sets)

    ''' For each process prepare a structure to host data '''
    for pid in range(1000,10): procset.append({pid[proc]*ts_sets})
    
    
    ''' Prepare a structure to host memory data '''
    
    
    #print("reserveMemory()", cpuIds)
    #print("reserveMemory()", cpuset)


def stopProcess(pid):
    '''
    Send the SIGSTOP signal to the process indicated by pid
    '''
    os.kill(int(pid), signal.SIGSTOP)
    # TODO: REMOVE AFTER DEMO
    print("Process [{}] stopped".format(pid))
    

def stopProcessGroup(pgid):
    '''
    Send the SIGSTOP signal to the process indicated by pid
    '''
    os.killpg(int(pgid), signal.SIGSTOP)
    # TODO: REMOVE AFTER DEMO
    print("Process group [{}] stopped".format(pgid))
    

def killProcess(pid):
    '''
    Send the SIGSTOP signal to the process indicated by pid
    '''
    os.kill(int(pid), signal.SIGKILL)
    # TODO: REMOVE AFTER DEMO
    print("Process [{}] killed".format(pid))
    

def killProcessGroup(pgid):
    '''
    Send the SIGSTOP signal to the process indicated by pid
    '''
    os.killpg(int(pgid), signal.SIGKILL)
    # TODO: REMOVE AFTER DEMO
    print("Process group [{}] killed".format(pgid))
    

def theshold_checker(pid):
    '''
    Manages processes that are overtaking the threshold limits
    '''
    global KILL_AFTER, pid_kill_counter

    # print("pid", pid)
    # print("pid_kill_counter", pid_kill_counter)

    if str(pid) in pid_kill_counter:
        pid_kill_counter[str(pid)] += 1
    else: 
        pid_kill_counter.update({str(pid): 1})
        
    if int(pid_kill_counter[str(pid)]) >= KILL_AFTER: stopProcess(pid)
    

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
        if float(prev["rss"]) == 0: 
            t_rss = 1.0
            p_rss = 0.0
        else: 
            t_rss = 1/(float(cpuStat["rss"])/float(prev["rss"]))
            p_rss = 0.0
            d_rss = (float(cpuStat["rss"])-float(prev["rss"]))
            if d_rss != 0: p_rss = 1/(tf/d_rss)
    except ValueError:
        t_rss = prev["rss"]
        p_rss = prev["p_rss"]
    try:
        if float(prev["softrss"]) == 0: 
            t_softrss = 1.0
            p_softrss = 0.0
        else: 
            t_softrss = 1/(float(cpuStat["softrss"])/float(prev["softrss"]))
            p_softrss = 0.0
            d_softrss = (float(cpuStat["softrss"])-float(prev["softrss"]))
            if d_softrss != 0: p_softrss = 1/(tf/d_softrss)
    except ValueError:
        t_softrss = prev["softrss"]
        p_softrss = prev["p_softrss"]
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
        "rss":cpuStat["rss"],
        "softrss":cpuStat["softrss"],
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
        "t_rss":t_rss,
        "p_rss":p_rss,
        "t_softrss":t_softrss,
        "p_softrss":p_softrss,
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
    try: rss = float(data[6].strip())
    except ValueError: rss = float(0.0)
    try: softrss = float(data[7].strip())
    except ValueError: softrss = float(0.0)
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
        "rss":rss,
        "softrss":softrss,
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
        "t_rss":float(0.0),
        "p_rss":float(0.0),
        "t_softrss":float(0.0),
        "p_softrss":float(0.0),
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
    Collect the metrics from /proc/stat
    '''
    global ts, prev_ts
    global poll_interval
    global cpuset, cpu

    labels = ["btime", "uptime", "processes", "procs_running", "procs_blocked"]
    cpus = []
    stat = {}
    
    with open('/proc/stat') as f:
        for line in f:
            cleanLine = line.replace("  ", " ")
            myLine = cleanLine.split(' ')
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
    Collect the metrics from /proc/meminfo
    '''
    labels = ["MemTotal", "MemFree", "MemAvailable", "SwapTotal", "SwapFree"]
    mem = {}
    
    with open('/proc/meminfo') as f:
        for line in f:
            myLine = line.split(':')
            if myLine[0].strip() in labels: mem[myLine[0].strip()] = myLine[1].strip()
    return mem


def procTrend(procStat, prev, tf):
    '''
    Calculate the difference between the current cpu stat and the previous one
    '''

    ''' If previous values are 0 then init to 1.0 the trend value and 0.0 the percentage one '''
    try:
        if float(prev["utime"]) == 0:
            p_utime = 0.0
        else: 
            p_utime = 0.0
            d_utime = (float(procStat["utime"])-float(prev["utime"]))
            if d_utime != 0: p_utime = 1/(tf/d_utime)
    except ValueError:
        p_utime = prev["p_utime"]
    try:
        if float(prev["stime"]) == 0: 
            p_stime = 0.0
        else: 
            p_stime = 0.0
            d_stime = (float(procStat["stime"])-float(prev["stime"]))
            if d_stime != 0: p_stime = 1/(tf/d_stime)
    except ValueError:
        p_stime = prev["p_stime"]
    try:
        if float(prev["cutime"]) == 0: 
            p_cutime = 0.0
        else: 
            p_cutime = 0.0
            d_cutime = (float(procStat["cutime"])-float(prev["cutime"]))
            if d_cutime != 0: p_cutime = 1/(tf/d_cutime)
    except ValueError:
        p_cutime = prev["p_cutime"]
    try:
        if float(prev["cstime"]) == 0: 
            p_cstime = 0.0
        else: 
            p_cstime = 0.0
            d_cstime = (float(procStat["cstime"])-float(prev["cstime"]))
            if d_cstime != 0: p_cstime = 1/(tf/d_cstime)
    except ValueError:
        p_cstime = prev["p_cstime"]
    try:
        if float(prev["vsize"]) == 0: 
            p_vsize = 0.0
        else: 
            p_vsize = 0.0
            d_vsize = (float(procStat["vsize"])-float(prev["vsize"]))
            if d_vsize != 0: p_vsize = 1/(tf/d_vsize)
    except ValueError:
        p_vsize = prev["p_vsize"]
    try:
        if float(prev["rss"]) == 0: 
            p_rss = 0.0
        else: 
            p_rss = 0.0
            d_rss = (float(procStat["rss"])-float(prev["rss"]))
            if d_rss != 0: p_rss = 1/(tf/d_rss)
    except ValueError:
        p_rss = prev["p_rss"]
    
    procStat = {
        "ts":procStat["ts"],
        "cmdline":procStat["cmdline"],
        "pid":procStat["pid"],
        "state":procStat["state"],
        "ppid":procStat["ppid"],
        "utime":procStat["utime"],
        "stime":procStat["stime"],
        "cutime":procStat["cutime"],
        "cstime":procStat["cstime"],
        "starttime":procStat["starttime"],
        "vsize":procStat["vsize"],
        "rss":procStat["rss"],
        "p_utime":p_utime,
        "p_stime":p_stime,
        "p_cutime":p_cutime,
        "p_cstime":p_cstime,
        "p_vsize":p_vsize,
        "p_rss":p_rss
    }
    #print("procTrend()", procStat)
    return procStat
    

def procsetAdd(pid, procStat):
    '''
    Append a proc stat vector to the procset list and calculate the trend compared
    to the previous timestamp
    '''
    global procset, ts_sets
    global POLL_HZ
    
    tf = POLL_HZ

    idx = -1
    for procDict in procset:
        idx += 1
        if procDict.has_key(pid):
            procDict[pid].insert(0, procTrend(procStat, procDict[pid][0], tf))
            #print("procDict", pid, procDict[pid])
            ''' If the queue is full, remove the oldest record '''
            if len(procDict[pid]) > ts_sets: del procDict[pid][-1]
            procset[idx] = {pid:procDict[pid]}
            #print("procset", idx, procset[idx])
            break
    
    #print("procsetAdd", procset[idx])
    #print("\procset\n", procset)
        
    
def procstat(cmdline, data):
    '''
    Parse process stats from the /proc/[pid]/stat output and assign values to global cpu
    
    Values are converted to float(0.0) in case the original value is not a 
    convertible number
    '''
    global ts, proc
    
    try: pid = int(data[0].strip())
    except ValueError: pid = int(0)
    
    state = str(data[2].strip())
    
    try: ppid = int(data[3].strip())
    except ValueError: ppid = int(0)
    try: utime = float(data[13].strip())
    except ValueError: utime = float(0.0)
    try: stime = float(data[14].strip())
    except ValueError: stime = float(0.0)
    try: cutime = float(data[15].strip())
    except ValueError: cutime = float(0.0)
    try: cstime = float(data[16].strip())
    except ValueError: cstime = float(0.0)
    try: starttime = float(data[21].strip())
    except ValueError: starttime = float(0.0)
    try: vsize = int(data[22].strip())
    except ValueError: vsize = int(0)
    try: rss = int(data[23].strip())
    except ValueError: rss = int(0)

    proc = {
        "ts":ts,                # Timestamp
        "cmdline":cmdline,
        "pid":pid,              #  1 The process ID
        "state":" ",            #  3 Process state (see man 5 proc)
        "ppid":ppid,            #  4 The PID of the parent of this process
        "utime":utime,          # 14 Amount of time scheduled in user mode
        "stime":stime,          # 15 Amount of time scheduled in kernel mode
        "cutime":cutime,        # 16 Amount of time waited-for children scheduled in user mode 
        "cstime":cstime,        # 17 Amount of time waited-for children scheduled in kernel mode 
        "starttime":starttime,  # 22 The time the process started after system boot 
        "vsize":vsize,          # 23 Virtual memory size in bytes
        "rss":rss,              # 24 Resident Set Size: number of pages the process has in real memory
        "p_utime":float(0.0),   # Percentage of time scheduled in user mode                      
        "p_stime":float(0.0),   # Percentage of time scheduled in kernel mode                    
        "p_cutime":float(0.0),  # Percentage of time waited-for children scheduled in user mode  
        "p_cstime":float(0.0),  # Percentage of time waited-for children scheduled in kernel mode
        "p_vsize":float(0.0),   # Percentage of virtual memory
        "p_rss":float(0.0)      # Percentage of the number of pages in real memory
    }
    #print("procStat()", cpuId, cpu)
    return pid, proc


def proc_stat():
    '''
    Collect the metrics from /proc/[pid]/stat
    '''
    global ts, prev_ts
    global poll_interval
    global procset, proc 
    global CPU_LIMIT, cpu_usage

    # Read all the process IDs in the /prod folder
    pid_list = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    
    for pid in pid_list:
        try:
            cmdline = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
            
            # TODO: REMOVE after demo
            # if "primes-cgi.py" in cmdline or "httpd" in cmdline:
            if "primes-cgi.py" in cmdline:
                # print("cmdline", str(cmdline))
                
                stat = open(os.path.join('/proc', pid, 'stat'), 'rb').read()
                # print("stat", str(stat))
                
                id, procStat = procstat(cmdline, stat)
                procsetAdd(id, procStat)
                
                if cpu_usage >= CPU_LIMIT: theshold_checker(pid)
                
        except IOError:
            continue
    
    '''
    procs = []
    stat = {}
    
    with open('/proc/stat') as f:
        for line in f:
            myLine = line.split(' ')
            if "cpu" in myLine[0].strip():
                cpuId, cpuStat = cpustat(myLine)
                cpusetAdd(cpuId, cpuStat)
            elif myLine[0].strip() in labels: stat[myLine[0].strip()] = myLine[1].strip()
    stat["uptime"] = time.time() - float(stat["btime"])
    '''
    ''' Store cpus stat in the time series set '''
    # for cpuId in cpus: cpuset = {ts:cpuId}
    
    # return stat


def main():
    '''
    '''
    try:
        global ts, prev_ts
        global poll_interval
        global cpuIds, cpuset, cpu, cpu_usage

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
                    if cpuKey == "cpu": cpu_usage = (cpuVal[0]["p_user"]*100)
                    print("{}\tuser: {} [{}]  nice: {} [{}]  system: {} [{}]  idle: {} [{}]  wait: {} [{}]".format(
                        cpuKey, 
                        "{0:.2f}".format((cpuVal[0]["p_user"]*100)), "{0:.2f}".format(cpuVal[1]["p_user"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_nice"]*100)), "{0:.2f}".format(cpuVal[1]["p_nice"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_system"]*100)), "{0:.2f}".format(cpuVal[1]["p_system"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_idle"]*100)), "{0:.2f}".format(cpuVal[1]["p_idle"]*100),
                        "{0:.2f}".format((cpuVal[0]["p_iowait"]*100)), "{0:.2f}".format(cpuVal[1]["p_iowait"]*100)
                        )
                )
            
            proc_stat()
            
            
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
