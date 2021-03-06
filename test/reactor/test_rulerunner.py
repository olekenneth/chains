import unittest
from chains.reactor.worker.context import Context
from chains.reactor.worker.rulerunner import RuleRunner
from chains.reactor.definition.event import Event
from chains.reactor.state import State
from chains.common import log
import rule1, rule2, rule3, rule4
import time

class TestRuleRunner(unittest.TestCase):

    def setUp(self):
        log.setLevel('debug')
        self.context = Context(State())
        # We use this as a poor man's MockAction. Rules will set keys here
        # to indicate how far in the rule's steps we've got to.
        self.context.test = {}

    # Simple tests where rule has one event

    def test_When_event_rule_waits_for_occurs_Rule_iterates_to_next_step(self):
        runner = RuleRunner('rule1', self.context, rule1, None)
        self.assertFalse( self.context.test.has_key('event-seen') )
        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()
        self.assertTrue( self.context.test.has_key('event-1.1-seen') )

    def test_When_event_rule_does_not_wait_for_occurs_Rule_does_not_iterate_to_next_step(self):
        runner = RuleRunner('rule1', self.context, rule1, None)
        self.assertFalse( self.context.test.has_key('event-seen') )
        runner.onEvent(Event(service='tellstick', key='switch-3'))
        runner.wait()
        self.assertFalse( self.context.test.has_key('event-1.1-seen') )

    def test_When_rule_has_no_more_events_It_is_complete(self):
        runner = RuleRunner('rule1', self.context, rule1, None)
        self.assertFalse(runner.isComplete)
        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()
        self.assertTrue(runner.isComplete)

    def test_When_rule_has_more_events_It_is_not_complete(self):
        runner = RuleRunner('rule1', self.context, rule1, None)
        self.assertFalse(runner.isComplete)
        runner.onEvent(Event(service='tellstick', key='switch-3'))
        runner.wait()
        self.assertFalse(runner.isComplete)

    def test_When_event_is_matched_The_yield_returns_the_event(self):
        runner = RuleRunner('rule4', self.context, rule4, None)
        self.assertFalse( self.context.test.has_key('matched-event') )
        runner.onEvent(Event(service='tellstick', key='switch-1', data={'value':'xyz', 'other': 'foo'}))
        runner.wait()
        self.assertTrue( self.context.test.has_key('matched-event') )
        self.assertEqual( self.context.test['matched-event'].key,           'switch-1' )
        self.assertEqual( self.context.test['matched-event'].data['value'], 'xyz' )
        self.assertEqual( self.context.test['matched-event'].data['other'], 'foo' )

    # More complex tests where rule has multiple events,
    # checks value in state, and runs callback on complete

    def test_When_rule_has_many_events_It_iterates_correctly(self):

        self.context.state.set('timer.hour.data.value', 17)
        runner = RuleRunner('rule2', self.context, rule2, None)

        # Before any events, rule does nothing
        self.assertFalse( self.context.test.has_key('event-2.1-seen') )
        self.assertFalse( self.context.test.has_key('event-2.2-seen') )
        self.assertFalse( self.context.test.has_key('event-2.3-seen') )

        # When event that is not in rule occurs, nothing happens
        runner.onEvent(Event(service='tellstick', key='foo'))
        runner.wait()
        self.assertFalse( self.context.test.has_key('event-2.1-seen') )
        self.assertFalse( self.context.test.has_key('event-2.2-seen') )
        self.assertFalse( self.context.test.has_key('event-2.3-seen') )

        # When event occurs that matches first event in rule, it iterates to next step
        runner.onEvent(Event(service='tellstick', key='switch-1'))
        runner.wait()
        self.assertTrue( self.context.test.has_key('event-2.1-seen') )
        self.assertFalse( self.context.test.has_key('event-2.2-seen') )
        self.assertFalse( self.context.test.has_key('event-2.3-seen') )

        # When another event that is not in rule occurs, nothing happens
        runner.onEvent(Event(service='tellstick', key='foo'))
        runner.wait()
        self.assertTrue( self.context.test.has_key('event-2.1-seen') )
        self.assertFalse( self.context.test.has_key('event-2.2-seen') )
        self.assertFalse( self.context.test.has_key('event-2.3-seen') )

        # When event occurs that matches second event in rule, it iterates another step
        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()
        self.assertTrue( self.context.test.has_key('event-2.2-seen') )
        self.assertFalse( self.context.test.has_key('event-2.3-seen') )

        # When event occurs that matches third event in rule, it iterates another step
        runner.onEvent(Event(service='tellstick', key='switch-3'))
        runner.wait()
        self.assertTrue( self.context.test.has_key('event-2.3-seen') )

    def test_When_rule_conditional_does_not_match_It_stops(self):

        # Rule checks hour >= 16 before last event, so when
        # hour is 15, it should only do event1 + event2

        self.context.state.set('timer.hour.data.value', 15)
        runner = RuleRunner('rule2', self.context, rule2, None)

        runner.onEvent(Event(service='tellstick', key='switch-1'))
        runner.wait()

        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()

        runner.onEvent(Event(service='tellstick', key='switch-3'))
        runner.wait()

        self.assertTrue( self.context.test.has_key('event-2.1-seen') )
        self.assertTrue( self.context.test.has_key('event-2.2-seen') )
        self.assertFalse( self.context.test.has_key('event-2.3-seen') )
    
    def test_When_rule_has_no_more_events_It_runs_complete(self):

        self.context.state.set('timer.hour.data.value', 17)
        runner = RuleRunner('rule2', self.context, rule2, None)

        self.assertFalse( self.context.test.has_key('complete') )

        runner.onEvent(Event(service='tellstick', key='switch-1'))
        runner.wait()

        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()

        self.assertFalse( self.context.test.has_key('complete') )

        runner.onEvent(Event(service='tellstick', key='switch-3'))
        runner.wait()

        self.assertTrue( self.context.test.has_key('complete') )

    def test_When_rule_stops_before_end_It_still_runs_complete(self):

        self.context.state.set('timer.hour.data.value', 15) # !!
        runner = RuleRunner('rule2', self.context, rule2, None)

        self.assertFalse( self.context.test.has_key('complete') )

        runner.onEvent(Event(service='tellstick', key='switch-1'))
        runner.wait()

        self.assertFalse( self.context.test.has_key('complete') )

        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()

        self.assertTrue( self.context.test.has_key('complete') )

    def test_When_rule_is_busy_It_does_not_process_events(self):

        runner = RuleRunner('rule3', self.context, rule3, None)

        # At this point, rule is waiting for events, so this event is processed
        runner.onEvent(Event(service='tellstick', key='switch-1'))

        # At this point, "action" from step 1 is running, and it takes 0.3 sec
        # so the event we send now should be ignored since rule is busy running action
        runner.onEvent(Event(service='tellstick', key='switch-2'))

        # Wait for action (step 1) to complete
        runner.wait()

        # Conclusion: Rule should have processed first event but not second
        self.assertTrue( self.context.test.has_key('event-3.1-seen') )
        self.assertFalse( self.context.test.has_key('event-3.2-seen') )

        # At this point rule is waiting for events again, so if we send
        # event 2 again now, it should be processed
        runner.onEvent(Event(service='tellstick', key='switch-2'))
        runner.wait()

        self.assertTrue( self.context.test.has_key('event-3.1-seen') )
        self.assertTrue( self.context.test.has_key('event-3.2-seen') )
    


if __name__ == '__main__':
    unittest.main()
