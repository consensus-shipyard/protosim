import logging
from typing import Annotated

from core import EventQueue, Network, Dispatcher, NodeId, InstanceId, Node, Simulator, Group, Protocol
from injection import Injector, Scope
from protocols.implementations import BroadcastPing


# Constructor for the Group of Nodes.
def build_nodes(injector: Injector, group: Group) -> list[Node]:
    nodes = []
    for node_id in group:
        injector.enter_node_scope(node_id)
        nodes.append(injector.get(Node))
        injector.exit_node_scope()
    return nodes


# Constructor for the Group (list of NodeIds).
def provide_node_ids(group_size: Annotated[int, 'group_size']) -> Group:
    return Group([NodeId(i) for i in range(group_size)])


# Main function. Sets up the injector and runs the simulator.
def main():
    logging.basicConfig(level=logging.DEBUG)

    injector = Injector()

    # Configure injector.
    injector.provide(EventQueue, scope=Scope.SINGLETON)
    injector.provide(Network, scope=Scope.SINGLETON)
    injector.provide(Dispatcher, scope=Scope.NODE)

    injector.supply(InstanceId, instance=InstanceId(id="root"))
    injector.supply(Annotated[NodeId, 'pinger'], NodeId(0))
    injector.provide(Annotated[Protocol, 'root'], constructor=BroadcastPing, scope=Scope.NODE)

    injector.supply(Annotated[int, 'group_size'], 4)
    injector.provide(Group, constructor=provide_node_ids, scope=Scope.SINGLETON)
    injector.provide(list[Node], constructor=build_nodes, scope=Scope.SINGLETON)

    injector.provide(Simulator, constructor=Simulator, scope=Scope.SINGLETON)

    # Run the simulator.
    simulator = injector.get(Simulator)
    simulator.run()


if __name__ == "__main__":
    main()
