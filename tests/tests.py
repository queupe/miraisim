# from io import StringIO
# import json
# import shutil
# import tempfile
from unittest import TestCase

import hosts
import targeting
import sim


class TestE2ELatency(TestCase):# {{{
    def setUp(self):
        self.min = 0.05
        self.max = 2.25
        self.timeout = 4.0
        self.maxhid = 100
        config = {'e2e_latency': {'min': self.min,
                                  'max': self.max,
                                  'timeout': self.timeout}}
        self.e2e_latency = hosts.E2ELatency(config)

    def test_timeout(self):
        self.assertEqual(self.e2e_latency.get_timeout(), self.timeout)

    def test_equality(self):
        for i in range(self.maxhid):
            for j in range(self.maxhid):
                if i == j: continue
                lat = self.e2e_latency.get(i, j)
                for _try in range(10):
                    self.assertEqual(self.e2e_latency.get(i, j), lat)

    def test_min_max(self):
        for i in range(self.maxhid):
            for j in range(self.maxhid):
                if i == j: continue
                lat = self.e2e_latency.get(i, j)
                self.assertTrue(lat >= self.min)
                self.assertTrue(lat <= self.max)

    def test_average(self):
        sx = 0
        for i in range(self.maxhid):
            for j in range(self.maxhid):
                if i == j: continue
                sx += self.e2e_latency.get(i, j)
        average = sx/(self.maxhid * (self.maxhid - 1))
        expected = (self.max - self.min)/2
        self.assertTrue(average >= expected - expected/2)
        self.assertTrue(average <= expected + expected/2)
# }}}


class TestTargetingFactory(TestCase):  # {{{
    def test_random_factory(self):
        maxhid = 10000
        config = {'targeting': {'class': 'RandomTargeting',
                                'params': []},
                  'maxhid': maxhid}

        factory = targeting.create_factory(config)
        self.assertTrue(isinstance(factory, targeting.RandomTargeting.Factory))

        instance1 = factory()
        self.assertTrue(isinstance(instance1, targeting.RandomTargeting))
        self.assertEqual(instance1.maxhid, maxhid)

        instance2 = factory()
        self.assertFalse(instance1 == instance2)

    def test_coordinated_factory(self):
        maxhid = 10000
        timeout = 600.0
        config = {'targeting': {'class': 'CoordinatedTargeting',
                                'params': [timeout]},
                  'maxhid': maxhid}

        factory = targeting.create_factory(config)
        self.assertTrue(isinstance(factory,
                                   targeting.CoordinatedTargeting.Factory))

        instance1 = factory()
        self.assertTrue(isinstance(instance1, targeting.CoordinatedTargeting))
        self.assertEqual(instance1.timeout, timeout)
        self.assertEqual(instance1.maxhid, maxhid)

        instance2 = factory()
        self.assertEqual(instance1, instance2)
# }}}


class TestRandomTargeting(TestCase):  # {{{
    def setUp(self):
        self.maxhid = 5
        config = {'targeting': {'class': 'RandomTargeting',
                                'params': []},
                  'maxhid': self.maxhid}
        self.factory = targeting.create_factory(config)

    def test_set_unreach(self):
        rnd = self.factory()
        for i in range(self.maxhid + 1):
            rnd.set_unreach(i)

        generated = set(rnd.get_target() for _i in range(self.maxhid * 1000))
        self.assertEqual(len(generated), self.maxhid + 1)

    def test_set_bot(self):
        rnd = self.factory()
        for i in range(self.maxhid + 1):
            rnd.set_bot(i)

        generated = set(rnd.get_target() for _i in range(self.maxhid * 1000))
        self.assertEqual(len(generated), self.maxhid + 1)

    def test_contains(self):
        rnd = self.factory()
        for i in range(self.maxhid + 1):
            rnd.set_bot(i)
            self.assertFalse(i in rnd)

    def test_distribution(self):
        rnd = self.factory()
        generated = list(rnd.get_target() for _i in range(self.maxhid * 1000))
        expected = self.maxhid/2
        average = sum(generated)/len(generated)
        self.assertTrue(average <= expected + expected/2)
        self.assertTrue(average >= expected - expected/2)
# }}}


class TestCoordinatedTargeting(TestCase):  # {{{
    def setUp(self):
        sim.now = 0
        self.maxhid = 10000
        self.timeout = 600.0
        config = {'targeting': {'class': 'CoordinatedTargeting',
                                'params': [self.timeout]},
                  'maxhid': self.maxhid}
        self.factory = targeting.create_factory(config)

    def test_set_unreach(self):
        rnd = self.factory()
        for i in range(0, self.maxhid + 1, 2):
            rnd.set_unreach(i)
            self.assertTrue(i in rnd)

        generated = set(rnd.get_target() for _i in range(self.maxhid * 100))
        self.assertTrue(len(generated) <= self.maxhid//2 + 1)
        for target in generated:
            self.assertTrue((target % 2) == 1)
            self.assertFalse(target in rnd)

    def test_set_bot(self):
        rnd = self.factory()
        for i in range(0, self.maxhid + 1, 2):
            rnd.set_unreach(i)
            self.assertTrue(i in rnd)

        generated = set(rnd.get_target() for _i in range(self.maxhid * 100))
        self.assertTrue(len(generated) <= self.maxhid//2 + 1)
        for target in generated:
            self.assertTrue((target % 2) == 1)
            self.assertFalse(target in rnd)

    def test_timeout(self):
        sim.now = 0.0
        rnd = self.factory()
        for i in range(0, self.maxhid + 1, 2):
            rnd.set_unreach(i)
            self.assertTrue(i in rnd)

        sim.now = self.timeout - 1
        for i in range(0, self.maxhid + 1, 2):
            self.assertTrue(i in rnd)

        sim.now = self.timeout + 1
        for i in range(0, self.maxhid + 1, 2):
            self.assertFalse(i in rnd)

    def test_timeout_reinsert(self):
        sim.now = 0.0
        rnd = self.factory()
        for i in range(0, self.maxhid + 1, 2):
            rnd.set_unreach(i)
            self.assertTrue(i in rnd)

        sim.now = 300.0
        for i in range(0, self.maxhid + 1, 2):
            rnd.set_unreach(i)
            self.assertTrue(i in rnd)

        sim.now = 300 + self.timeout - 1
        for i in range(0, self.maxhid + 1, 2):
            self.assertTrue(i in rnd)

        sim.now = 300 + self.timeout + 1
        for i in range(0, self.maxhid + 1, 2):
            self.assertFalse(i in rnd)

    def test_no_targets(self):
        rnd = self.factory()
        for i in range(0, self.maxhid + 1):
            rnd.set_unreach(i)
            self.assertTrue(i in rnd)
        target = rnd.get_target()


        
# }}}


class TestHost(TestCase):# {{{
    def setUp(self):
        sim.now = 0.0
        sim.evqueue = list()
        sim.dist_host_on_time = lambda: 5.0
        sim.dist_host_off_time = lambda: 5.0
        self.frac_vulnerable = 0.5
        self.maxhid = 5
        config = {'frac_vulnerable': self.frac_vulnerable,
                  'maxhid': self.maxhid}
        sim.host_tracker = hosts.HostTracker(config)

    def test_vulnerable_period(self):
        self.assertEqual(sim.host_tracker.vulnerable_period, 2)

    def test_bootup_shutdown(self):
        self.assertEqual(len(sim.evqueue), 0)
        self.assertEqual(sim.now, 0.0)

        hosts.Host.bootup(0)
        host0, status = sim.host_tracker.get(0)
        self.assertEqual(host0.hid, 0)
        self.assertEqual(status, hosts.STATUS_VULNERABLE)
        self.assertEqual(host0.on_time, 5.0)
        self.assertEqual(len(sim.evqueue), 1)

        hosts.Host.bootup(2)
        host2, status = sim.host_tracker.get(2)
        self.assertEqual(host2.hid, 2)
        self.assertEqual(status, hosts.STATUS_VULNERABLE)
        self.assertEqual(host2.on_time, 5.0)
        self.assertEqual(len(sim.evqueue), 2)

        tstamp, fn, data = sim.dequeue()  # host0.shutdown
        self.assertEqual(tstamp, 5.0)
        self.assertEqual(fn, host0.shutdown)
        self.assertIsNone(data)

        fn(data)
        self.assertEqual(len(sim.evqueue), 2)  # host0.bootup event added

        host0, status = sim.host_tracker.get(0)
        self.assertIsNone(host0)
        self.assertEqual(status, hosts.STATUS_SHUTDOWN)

        tstamp, fn, data = sim.dequeue()  # ignore host2.shutdown
        tstamp, fn, data = sim.dequeue()  # host0.bootup
        self.assertEqual(tstamp, 10.0)
        self.assertEqual(fn, hosts.Host.bootup)
        self.assertEqual(data, 0)

        fn(data)
        self.assertEqual(len(sim.evqueue), 1)  # host0.shutdown event added

    def test_statuses(self):
        hosts.Host.bootup(0)
        with self.assertRaises(AssertionError):
            hosts.Host.bootup(1)
        host0, status0 = sim.host_tracker.get(0)
        host1, status1 = sim.host_tracker.get(1)
        host2, status2 = sim.host_tracker.get(2)
        host3, status3 = sim.host_tracker.get(3)
        self.assertEqual(host0.status, hosts.STATUS_VULNERABLE)
        self.assertEqual(status0, hosts.STATUS_VULNERABLE)
        self.assertIsNone(host1)
        self.assertEqual(status1, hosts.STATUS_SECURE)
        self.assertIsNone(host2)
        self.assertEqual(status2, hosts.STATUS_SHUTDOWN)
        self.assertIsNone(host3)
        self.assertEqual(status3, hosts.STATUS_SECURE)
# }}}

