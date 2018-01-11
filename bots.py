import logging

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
        self.targeting = sim.targeting_factory()
        self.status = STATUS_CREATED

    def start(self):
        logging.debug('%s rate %f', self, self.rate)
        assert self.status == STATUS_CREATED
        self.status = STATUS_ACTIVE
        ev = (sim.now, self.attempt_auth, None)
        sim.enqueue(ev)

    def attempt_auth(self, _data):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%s teardown abort', self)
            return
        ev = (sim.now + 1/self.rate, self.attempt_auth, None)
        sim.enqueue(ev)

        dsthid = self.targeting.get_target()
        _host, status = sim.host_tracker.get(dsthid)
        logging.debug('%s dst %d status %s', self, dsthid, status)

        if status in [hosts.STATUS_SECURE,
                      hosts.STATUS_SHUTDOWN,
                      hosts.STATUS_INFECTED]:
            self.targeting.set_unreach(dsthid)
        elif status in [hosts.STATUS_VULNERABLE]:
            delay = sim.e2e_latency.get_auth_delay((self.hid, dsthid))
            # cunha @20180111.1335 not sure we need this FIXME
            # include infect delay:
            # delay += sim.e2e_latency.get_infect_delay((self.hid, dsthid))
            ev = (sim.now + delay, self.attempt_infect, dsthid)
            sim.enqueue(ev)

    def attempt_infect(self, hid):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%s teardown abort', self)
            return

        host, status = sim.host_tracker.get(hid)
        logging.debug('%s dst %d status %s', self, hid, status)

        if hid in self.targeting:
            logging.debug('%s dst %d in-cache abort', self, hid)
        elif status in [hosts.STATUS_SECURE,
                        hosts.STATUS_SHUTDOWN,
                        hosts.STATUS_INFECTED]:
            logging.debug('%s dst %d unreachable failure', self, hid)
            self.targeting.set_unreach(hid)
        elif status in [hosts.STATUS_VULNERABLE]:
            logging.debug('%s dst %d infect success', self, hid)
            self.targeting.set_bot(hid)
            host.infect()

    def teardown(self):
        self.status = STATUS_TEARDOWN

    def __str__(self):
        return 'Bot %d' % self.hid
# }}}


class MultiThreadBot(object):# {{{
    class Factory(object):# {{{
        def __init__(self, config):
            assert len(config['bot']['params']) == 1
            self.nthreads = float(config['bot']['params'][0])
        def __call__(self, hid):
            return MultiThreadBot(hid, self.nthreads)
    # }}}

    def __init__(self, hid, nthreads):
        self.hid = int(hid)
        self.nthreads = int(nthreads)
        self.targeting = sim.targeting_factory()
        self.status = STATUS_CREATED

    def start(self):
        logging.debug('%s nthreads %d', self, self.nthreads)
        assert self.status == STATUS_CREATED
        self.status = STATUS_ACTIVE
        for _i in range(self.nthreads):
            ev = (sim.now, self.attempt_auth, None)
            sim.enqueue(ev)

    def attempt_auth(self, _data):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%s teardown abort', self)
            return

        dsthid = self.targeting.get_target()
        _host, status = sim.host_tracker.get(dsthid)
        logging.debug('%s dst %d status %s', self, dsthid, status)

        delay = sim.e2e_latency.get_auth_delay((self.hid, dsthid))
        if status in [hosts.STATUS_SECURE,
                      hosts.STATUS_SHUTDOWN,
                      hosts.STATUS_INFECTED]:
            self.targeting.set_unreach(dsthid)
            ev = (sim.now + delay, self.attempt_auth, None)
            sim.enqueue(ev)
        elif status in [hosts.STATUS_VULNERABLE]:
            ev = (sim.now + delay, self.attempt_infect, dsthid)
            sim.enqueue(ev)

    def attempt_infect(self, hid):
        if self.status == STATUS_TEARDOWN:
            logging.debug('%s teardown abort', self)
            return

        host, status = sim.host_tracker.get(hid)
        logging.debug('%s dst %d status %s', self, hid, status)

        if hid in self.targeting:
            logging.debug('%s dst %d in-cache abort', self, hid)
            delay = 0
        elif status in [hosts.STATUS_SECURE,
                        hosts.STATUS_SHUTDOWN,
                        hosts.STATUS_INFECTED]:
            logging.debug('%s dst %d unreachable failure', self, hid)
            self.targeting.set_unreach(hid)
            delay = sim.e2e_latency.get_auth_delay((self.hid, hid))
        elif status in [hosts.STATUS_VULNERABLE]:
            logging.debug('%s dst %d infect success', self, hid)
            self.targeting.set_bot(hid)
            host.infect()
            delay = sim.e2e_latency.get_infect_delay((self.hid, hid))

        ev = (sim.now + delay, self.attempt_auth, None)
        sim.enqueue(ev)

    def teardown(self):
        self.status = STATUS_TEARDOWN

    def __str__(self):
        return 'Bot %d' % self.hid
# }}}
