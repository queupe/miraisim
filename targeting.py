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
        return random.randint(0, self.maxhid)

    def set_unreach(self, hid):
        pass

    def set_bot(self, hid):
        pass

    def __contains__(self, hid):
        return False

    def __str__(self):
        return 'RandomTargets maxhid %d' % self.maxhid
# }}}


class CoordinatedTargeting(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['targeting']['params']) == 1
            timeout = float(config['targeting']['params'][0])
            maxhid = int(config['maxhid'])
            self.unique = CoordinatedTargeting(timeout, maxhid)
        def __call__(self):
            return self.unique
    # }}}
    class TargetSet(object):# {{{
        def __init__(self):
            self.hid2pos = dist()
            self.hids = list()
        def add(self, hid):
            if hid not in self.hid2pos:
                self.hid2pos[hid] = len(self.hids)
                self.hids.append(hid)
        def remove(self, hid):
            if hid in self.hid2pos:
                pos = self.hid2pos.pop(hid)
                last = self.hids.pop()
                if hid != last:  # pos != len(self.hids)
                    self.hids[pos] = last
                    self.hid2pos[last] = pos
        def choice(self): return random.choice(self.hids)
        def __contains__(self, hid): return hid in self.hid2pos
        def __len__(self): return len(self.hids)
        def __str__(self): return 'TargetSet size %d' % len(self.hids)
    # }}}

    def __init__(self, timeout, maxhid):
        self.timeout = float(timeout)
        self.timestamps = collections.deque()
        self.targets = TargetSet()
        for i in range(maxhid+1):
            self.targets.add(i)

    def get_target(self):
        self.__contains__(0)  # remove timed-out entries
        return self.targets.choice()

    def set_unreach(self, hid):
        self.timeouts.append((sim.now, hid))
        self.targets.remove(hid)

    def set_bot(self, hid):
        self.timeouts.append((sim.now, hid))
        self.targets.remove(hid)

    def __contains__(self, hid):
        while (self.timestamps and
               sim.now - self.timestamps[0][0] > self.timeout):
            _tstamp, timed_out_hid = self.timestamps.popleft()
            self.targets.add(timed_out_hid)
        return hid not in self.targets

    def __str__(self):
        return 'CoordinatedTargeting maxhid %d timeout %f (%s)' % (
                self.maxhid, self.timeout, self.targets)
# }}}

