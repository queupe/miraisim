import random


def create_factory(config):
    name = config['botcache']['class']
    globals()[name].Factory(config)


class NullCache(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['botcache']['params']) == 0
            self.maxhid = int(config['maxhid'])
        def __call__(self):
            return NullCache(self.maxhid)
    # }}}

    def __init__(self, maxhid):
        self.maxhid = int(maxhid)

    def get_target(self):
        return random.randint(0, self.maxhid)

    def set_unreach(self, hid):
        pass

    def set_bot(self, hid):
        pass

    def __str__(self):
        return 'NullCache maxhid %d' % self.maxhid
# }}}


class LocalTimeoutCache(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['botcache']['params']) == 1
            self.timeout = float(config['botcache']['params'][0])
            self.maxhid = int(config['maxhid'])
        def __call__(self):
            return LocalTimeoutCache(self.timeout, self.maxhid)
    # }}}

    def __init__(self, timeout, maxhid):
        self.timeout = float(timeout)
        self.maxhid = int(maxhid)
        self.hid2tstamp = dict()

    def get_target(self):
        hid = random.randint(1, self.maxhid - 1)
        # stop iteration at the previous hid:
        end = (hid + self.maxhid - 1) % self.maxhid
        while hid in self.hid2tstamp and hid != end:
            if sim.now - self.hid2tstamp[hid] > self.timeout:
                del self.hid2tstamp[hid]
                return hid
            hid = (hid + 1) % self.maxhid
        return hid

    def set_unreach(self, hid):
        self.hid2tstamp[hid] = sim.now

    def set_bot(self, hid):
        self.hid2tstamp[hid] = sim.now

    def __str__(self):
        return 'LocalTimeoutCache maxhid %d timeout %f size %d' % (
                self.maxhid, self.timeout, len(self.hid2tstamp))
# }}}


class GlobalTimeoutCache(object):# {{{
    class Factory(object):
        def __init__(self, config):
            assert len(config['botcache']['params']) == 1
            timeout = float(config['botcache']['params'][0])
            self.cache = LocalTimeoutCache(timeout, config['maxhid'])
        def __call__(self):
            return self.cache
# }}}
