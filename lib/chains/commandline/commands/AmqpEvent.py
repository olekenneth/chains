from chains.commandline.commands import Command

class CommandAmqpEvent(Command):
    def main(self, serviceId, key, value):
        """ Inject an event on message bus """
        event = {'service': serviceId, 'key': key, 'data': {'value':value}}
        self.connection.producer(queuePrefix='chainsadmin-amqp-event').put('de.%s.%s' % (serviceId, key), event)
        return "Sent event: %s" % event
