from dataclasses import dataclass

from injector import inject

from core import Message, node
from protocols.types.broadcast import ConsistentBroadcast


@node
@inject
@dataclass
class EchoConsistentBroadcast(ConsistentBroadcast):
    def start(self):
        pass

    def deliver(self, msg: Message):
        pass
