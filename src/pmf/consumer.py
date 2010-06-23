#
# Copyright (c) 2010 Red Hat, Inc.
#
# Authors: Jeff Ortel <jortel@redhat.com>
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

"""
Provides AMQP message consumer classes.
"""

from qpid.util import connect
from qpid.connection import Connection
from qpid.datatypes import Message, RangedSet, uuid4
from qpid.queue import Empty

class Consumer:
    """
    An AMQP consumer.
    @ivar queue: The primary incoming message queue.
    @type queue: L{qpid.Queue}
    @ivar session: An AMQP session.
    @type session: L{qpid.Session}
    """

    def __init__(self, id, host='localhost', port=5672):
        """
        @param host: The fqdn or IP of the QPID broker.
        @type host: str
        @param port: The port of the QPID broker.
        @type port: short
        """
        socket = connect(host, port)
        connection = Connection(sock=socket)
        connection.start()
        sid = str(uuid4())
        session = connection.session(sid)
        session.queue_declare(queue=id, exclusive=True)
        session.exchange_bind(
            exchange='amq.match',
            queue=id,
            binding_key=id,
            arguments={'x-match':'any','consumerid':id})
        session.message_subscribe(queue=id, destination=id)
        self.queue = session.incoming(id)
        self.session = session

    def start(self, dispatcher):
        """
        Start processing messages on the queue using the
        specified dispatcher.
        @param dispatcher: An RMI dispatcher.
        @type dispatcher: L{pmf.Dispatcher}
        @return: self
        @rtype: L{Consumer}
        """
        self.queue.start()
        while True:
            try:
                message = self.queue.get(timeout=10)
                content = message.body
                self.session.message_accept(RangedSet(message.id))
                reply = dispatcher.dispatch(content)
                self.__respond(message, reply)
            except Empty:
                pass

    def __respond(self, message, content):
        """
        Respond to request with the specified I{content}.
        A response is send B{only} when a I{replyto} is specified
        in the I{message}.
        @param message: An AMQP (request) message.
        @type message: L{Message}
        @param content: A json encoded reply
        @type content: str
        """
        mp = message.get("message_properties")
        if mp.reply_to is None:
            return
        dest = mp.reply_to.exchange
        key = mp.reply_to.routing_key
        dp = self.session.delivery_properties(routing_key=key)
        reply = Message(dp, content)
        self.session.message_transfer(destination=dest, message=reply)
        return self
