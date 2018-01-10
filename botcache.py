import collections
import random


def create_factory(config):
    name = config['botcache']['class']
    return globals()[name].Factory(config)


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
        return random.randint(1, self.maxhid - 1)

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
            self.shared_targets = set(i for i in range(1, self.maxhid))
        def __call__(self):
            return LocalTimeoutCache(self.timeout, self.shared_targets)
    # }}}

    def __init__(self, timeout, shared_targets):
        self.timeout = float(timeout)
        self.shared_targets = shared_targets
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

    def __contains__(self, hid):
        while sim.now - self.timestamps[0][0] > self.timeout:
            tstamp, hid = self.timestamps.popleft()
            self.hids.discard(hid)
        return hid in self.hids

    def __str__(self):
        return 'LocalTimeoutCache maxhid %d timeout %f size %d' % (
                self.maxhid, self.timeout, len(self.hid2tstamp))
# }}}


class GlobalTimeoutCache(object):# {{{
    class Factory(object):
        def __init__(self, config):
            assert len(config['botcache']['params']) == 1
            timeout = float(config['botcache']['params'][0])
            shared_targets = set(i for i in range(1, self.maxhid))
            self.cache = LocalTimeoutCache(timeout, shared_targets)
        def __call__(self):
            return self.cache
# }}}

