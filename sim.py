import heapq

config = dict()
host_tracker = None
e2e_latency = None
bot_factory = None
targeting_factory = None
dist_host_on_time = None
dist_host_off_time = None

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
