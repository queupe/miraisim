import heapq


_SHUTDOWN_ = 0
_SUSCETIBLE_ = 1
_INFECTED_ = 2

count_history = list()
#count_off_history = list()
#count_heal = list()
#count_time_status = list()
hist_infect = list()

config = dict()
host_tracker = None
e2e_latency = None
bot_factory = None
targeting_factory = None
dist_host_on_time = None
dist_host_off_time = None

heal_hosts = 0
infected_hosts = 0
off_hosts = 0

attempt_infected_endogeno = 0
attempt_infected_exogeno = 0

now = 0
evqueue = list()
evseq = 0


def enqueue(ev):
    # Assumes ev = (time, fn, fndata)
    assert ev[0] >= now
    global evseq
    heapq.heappush(evqueue, (ev[0], evseq, ev[1], ev[2]))
    evseq += 1


def dequeue():
    global now
    now, _evseq, fn, data = heapq.heappop(evqueue)
    return (now, fn, data)


def add_infected_host(hid):
    global now
    global infected_hosts
    global heal_hosts
    global off_hosts
    global count_history

    infected_hosts = infected_hosts + 1
    if heal_hosts > 0:
        heal_hosts -= 1

    inf_hist = (heal_hosts,infected_hosts, off_hosts, now, hid,_INFECTED_,_SUSCETIBLE_)
    count_history.append(inf_hist)

def add_attempt_infect(hid_source, hid_target, status, success):
    global attempt_infected_exogeno
    global attempt_infected_endogeno
    global hist_infect
    global now

    #print("Temp to infect {:d} -> {:d} : Status:{}".format(hid_source, hid_target, status))
    hist_infect.append((now, hid_source, hid_target, success))
    if (hid_source == 0):
        attempt_infected_exogeno = attempt_infected_exogeno + 1
    else:
        attempt_infected_endogeno = attempt_infected_endogeno + 1


def add_off_host(hid, Infected = False, on_time = 0, infec_time = 0):
    global now
    global heal_hosts
    global infected_hosts
    global off_hosts
    #global count_time_status
    global count_history
    status_before = _SUSCETIBLE_
    if Infected:
        if infected_hosts > 0:
            infected_hosts = infected_hosts - 1
        status_before = _INFECTED_
        #inf_hist = (infected_hosts, now, hid,_INFECTED_)
        #count_history.append(inf_hist)
    elif(heal_hosts > 0):
        heal_hosts -= 1
    off_hosts = off_hosts + 1
    off_hist = (off_hosts, now, hid)
    #count_off_history.append(off_hist)
    #count_time_status.append((hid, on_time - infec_time))

    inf_hist = (heal_hosts,infected_hosts, off_hosts, now, hid,_SHUTDOWN_,status_before)
    count_history.append(inf_hist)


def add_on_host(hid):
    global now
    global heal_hosts
    global infected_hosts
    global off_hosts
    global count_history

    if off_hosts > 0:
        off_hosts = off_hosts - 1

    heal_hosts += 1
    #off_hist = (off_hosts, now, hid)
    #count_off_history.append(off_hist)

    inf_hist = (heal_hosts,infected_hosts, off_hosts, now, hid,_SUSCETIBLE_,_SHUTDOWN_)
    count_history.append(inf_hist)
