from typing import Annotated

from core import InstanceId, NodeId, Protocol
from injection import Factory, Injector, Scope
from injection.injector import AbstractModule
from protocols.implementations import BroadcastPing


class BroadcastPingModule(AbstractModule):
    @staticmethod
    def provide_root_protocol(factory: Factory[BroadcastPing]) -> BroadcastPing:
        return factory.create(instance_id=InstanceId(id="root"), pinger=NodeId(0))

    def configure(self, injector: Injector):
        injector.provide(Annotated[Protocol, 'root'], constructor=self.provide_root_protocol, scope=Scope.NODE)
