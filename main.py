import dataclasses
from typing import Annotated, Protocol

from core import EventQueue, Network, Dispatcher, NodeId, InstanceId, Node, Simulator, Group
from injector import Injector, Scope
from protocols.implementations import EchoConsistentBroadcast


# Constructor for the Group of Nodes.
def build_group(injector: Injector, group_size: Annotated[int, 'group_size']) -> Group:
    group = Group([])
    for i in range(group_size):
        injector.enter_node_scope(NodeId(i))
        group.append(injector.get(Node))
        injector.exit_node_scope()
    return group


# Main function. Sets up the injector and runs the simulator.
def main():
    injector = Injector()

    # Configure injector.
    injector.provide(EventQueue, scope=Scope.SINGLETON)
    injector.provide(Network, scope=Scope.SINGLETON)
    injector.provide(Dispatcher, scope=Scope.NODE)

    injector.supply(InstanceId, instance=InstanceId(("root", 0)))
    injector.provide(Annotated[Protocol, 'root'], constructor=EchoConsistentBroadcast, scope=Scope.NODE)

    injector.supply(Annotated[int, 'group_size'], 2)
    injector.provide(Group, constructor=build_group, scope=Scope.SINGLETON)

    injector.provide(Simulator, constructor=Simulator, scope=Scope.SINGLETON)

    # Run the simulator.
    simulator = injector.get(Simulator)
    simulator.run()


if __name__ == "__main__":
    main()
