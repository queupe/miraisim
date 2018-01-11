import collections
import random


def create_factory(config):
    name = config['targeting']['class']
    return globals()[name].Factory(config)


class RandomTargeting(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['targeting']['params']) == 0
            self.maxhid = int(config['maxhid'])
        def __call__(self):
            return RandomTargeting(self.maxhid)
    # }}}

    def __init__(self, maxhid):
        self.maxhid = int(maxhid)

    def get_target(self):
        return random.randint(0, self.maxhid - 1)

    def set_unreach(self, hid):
        pass

    def set_bot(self, hid):
        pass

    def __str__(self):
        return 'RandomTargets maxhid %d' % self.maxhid
# }}}


class CoordinatedTargeting(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['targeting']['params']) == 1
            timeout = float(config['targeting']['params'][0])
            self.maxhid = int(config['maxhid'])
            self.cache = CoordinatedTargeting(timeout, maxhid)
        def __call__(self):
            return self.cache
    # }}}
    class ListDict(object):# {{{
        def __init__(self, timeout):
            self.timeout = float(timeout)
            self.hid2pos = dist()
            self.hids = list()
        def add(self, hid):
            if hid in self.hid2pos:
                self.hids[self.hid2pos[hid]] = (hid, sim.now)
            else:
                self.hid2pos[hid] = len(self.hids)
                self.hids.append((hid, sim.now))
        def choice(self):
            hid = random.choice(self.hids)
            while hid not in self:
                hid = random.choice(self.hids)
            return hid
        def __contains__(self, hid):
            if hid in self.hid2pos:
                pos = self.hid2pos[hid]
                _hid, tstamp = self.hids[pos]
                if sim.now - tstamp > self.timeout:
                    del self.hid2pos[hid]
                    lasthid, lasttstamp = self.hids.pop()
                    if pos != len(self.hids):
                        self.hids[pos] = (lasthid, laststamp)
                        self.hid2pos[lasthid] = pos
            return hid in self.hid2pos
    # }}}

    def __init__(self, timeout, maxhid):
        self.targets = ListDict()
        for i in range(maxhid):
            self.targets.add(i)
        self.timeout = float(timeout)
        self.hids = set()
        self.timestamps = collections.deque()

    def get_target(self):
        self.__contains__(0)  # remove timed-out entries
        random.choice(self.shared_targets - self.hids)

    def set_unreach(self, hid):
        self.timeouts.append((sim.now, hid))
        self.hids.add(hid)

    def set_bot(self, hid):
        self.timeouts.append((sim.now, hid))
        self.hids.add(hid)

    def __str__(self):
        return 'LocalTimeoutCache maxhid %d timeout %f size %d' % (
                self.maxhid, self.timeout, len(self.hid2tstamp))

# }}}

