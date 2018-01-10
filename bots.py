import heapq
import logging

import botcache
import hosts

import sim


STATUS_ACTIVE = 'bot_status_active'
STATUS_CREATED = 'bot_status_created'
STATUS_TEARDOWN = 'bot_status_teardown'


def create_factory(config):
    name = config['bot']['class']
    return globals()[name].Factory(config)



class FixedRateBot(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['bot']['params']) == 1
            self.rate = float(config['bot']['params'][0])
        def __call__(self, hid):
            return FixedRateBot(hid, self.rate)
    # }}}

    def __init__(self, hid, rate):
        self.hid = int(hid)
        self.rate = float(rate)
        self.cache = sim.botcache_factory()
        self.status = STATUS_CREATED

    def start(self):
        logging.debug('%.6f %s start', sim.now, self)
        assert self.status == STATUS_CREATED
        self.status = STATUS_ACTIVE
        self.attempt_auth(None)

    def attempt_auth(self, _data):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%.6f %s attempt_auth teardown abort', sim.now, self)
            return

        ev = (sim.now + 1/self.rate, self.attempt_auth, None)
        sim.enqueue(ev)

        dsthid = self.cache.get_target()
        host, status = sim.host_tracker.get(dsthid)
        logging.debug('%.6f %s attempt_auth dst %d status %s',
                      sim.now, self, dsthid, status)

        if status == hosts.STATUS_SECURE:
            self.cache.set_unreach(dsthid)
        elif status == hosts.STATUS_SHUTDOWN:
            self.cache.set_unreach(dsthid)
        elif status == hosts.STATUS_INFECTED:
            self.cache.set_unreach(dsthid)
        elif status == hosts.STATUS_VULNERABLE:
            delay = sim.e2e_latency.get_auth_delay((self.hid, dsthid))
            # include infect delay:
            delay += sim.e2e_latency.get_infect_delay((self.hid, dsthid))
            ev = (sim.now + delay, self.attempt_infect, host)
            sim.enqueue(ev)

    def attempt_infect(self, host):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%.6f %s attempt_infect teardown abort', sim.now, self)
            return
        self.cache.set_bot(host.hid)
        host.infect()
        logging.debug('%.6f %s attempt_infect dst %d', sim.now, self, host.hid)

    def teardown(self):
        self.status = STATUS_TEARDOWN

    def __str__(self):
        return 'Bot %d (%s)' % (self.hid, self.cache)
# }}}


class MultiThreadBot(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['bot']['params']) == 1
            self.nthreads = float(config['bot']['params'][0])
        def __call__(self, hid):
            return MultiThreadBot(hid, self.nthreads)
    # }}}

    def __init__(self, hid, rate):
        self.hid = int(hid)
        self.rate = float(rate)
        self.cache = sim.botcache_factory()
        self.status = STATUS_CREATED

    def start(self):
        logging.debug('%.6f %s start', sim.now, self)
        assert self.status == STATUS_CREATED
        self.status = STATUS_ACTIVE
        for _i in range(self.nthreads):
            ev = (sim.now, self.attempt_auth, None)
            sim.enqueue(ev)

    def attempt_auth(self, _data):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%.6f %s attempt_auth teardown abort', sim.now, self)
            return
        dsthid = self.cache.get_target()
        host, status = sim.host_tracker.get(dsthid)
        logging.debug('%.6f %s attempt_auth dst %d status %s',
                      sim.now, self, dsthid, status)
        delay = sim.e2e_latency.get_auth_delay((self.hid, dsthid))
        if status in [hosts.STATUS_SECURE,
                      hosts.STATUS_SHUTDOWN,
                      hosts.STATUS_INFECTED]:
            self.cache.set_unreach(dsthid)
            ev = (sim.now + delay, self.attempt_auth, None)
            sim.enqueue(ev)
        elif status == hosts.STATUS_VULNERABLE:
            ev = (sim.now + delay, self.attempt_infect, host)
            sim.enqueue(ev)

    def attempt_infect(self, hid):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%.6f %s attempt_infect teardown abort', sim.now, self)
            return
        host, status = sim.host_tracker.get(hid)
        logging.debug('%.6f %s attempt_infect dst %d status %s',
                      sim.now, self, hid, status)
        delay = -1
        if hid in self.cache:
            logging.debug('%.6f %s attempt_infect dst in cache')
            delay = 0
        elif status in [hosts.STATUS_SECURE,
                        hosts.STATUS_SHUTDOWN,
                        hosts.STATUS_INFECTED]:
            self.cache.set_unreach(hid)
            delay = sim.e2e_latency.get_auth_delay((self.hid, hid))
        elif status == hosts.STATUS_VULNERABLE:
            self.cache.set_bot(hid)
            host.infect()
            delay = sim.e2e_latency.get_infect_delay((self.hid, hid))
        ev = (sim.now + delay, self.attempt_auth, None)
        sim.enqueue(ev)

    def teardown(self):
        self.status = STATUS_TEARDOWN

    def __str__(self):
        return 'Bot %d (%s)' % (self.hid, self.cache)
# }}}
