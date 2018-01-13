import logging
import random

import sim


def create_factory(config):
    name = config['targeting']['class']
    if name not in globals():
        msg = 'unknown bot targeting strategy (%s)' % name
        logging.fatal(msg)
        raise ValueError(msg)
    return globals()[name].Factory(config)


class RandomTargeting(object):  # {{{
    class Factory(object):  # {{{
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


class CoordinatedTargeting(object):  # {{{
    class Factory(object):  # {{{
        def __init__(self, config):
            assert len(config['targeting']['params']) == 1
            timeout = float(config['targeting']['params'][0])
            maxhid = int(config['maxhid'])
            self.unique = CoordinatedTargeting(timeout, maxhid)

        def __call__(self):
            return self.unique
    # }}}

    class TargetSet(object):  # {{{
        def __init__(self):
            self.hid2pos = dict()
            self.hids = list()

        def add(self, hid):
            logging.debug('hid %d', hid)
            if hid not in self.hid2pos:
                self.hid2pos[hid] = len(self.hids)
                self.hids.append(hid)

        def remove(self, hid):
            logging.debug('hid %d', hid)
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
        self.maxhid = int(maxhid)
        self.hid2tstamp = dict()
        self.targets = CoordinatedTargeting.TargetSet()
        for i in range(self.maxhid + 1):
            self.targets.add(i)

    def get_target(self):
        target = self.targets.choice()
        while target in self:
            target = self.targets.choice()
        return target

    def set_unreach(self, hid):
        self.hid2tstamp[hid] = sim.now
        self.targets.remove(hid)

    def set_bot(self, hid):
        self.hid2tstamp[hid] = sim.now
        self.targets.remove(hid)

    def __contains__(self, hid):
        if sim.now - self.hid2tstamp.get(hid, sim.now) > self.timeout:
            self.hid2tstamp.pop(hid)
            self.targets.add(hid)
        return hid in self.hid2tstamp

    def __str__(self):
        return 'CoordinatedTargeting maxhid %d timeout %f cachesize %d' % \
            (self.maxhid, self.timeout, len(self.hid2tstamp))
# }}}
