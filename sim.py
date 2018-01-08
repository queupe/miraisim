import heapq

config = None

now = 0
evqueue = list()
evseq = 0

create_bot_fn = None
create_bot_cache_fn = None

def compute_latency(srchid, dsthid):
    return 10.0

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
