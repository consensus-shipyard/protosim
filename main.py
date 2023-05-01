from injector import Module, Injector, singleton, multiprovider, ClassAssistedBuilder, provider, SingletonScope

from core import EventQueue, Network, Node, Group, NodeId, NodeScope, InstanceId, Simulator, node, RootProtocol
from protocols.implementations import EchoConsistentBroadcast


class SimpleModule(Module):
    def configure(self, binder):
        binder.bind(InstanceId, to=lambda: InstanceId(('root', 0)))

    @node
    @provider
    def provide_for_root(self, eb: EchoConsistentBroadcast) -> RootProtocol:
        return eb

    @node
    @singleton
    @provider
    def provide_node_id(self, node_scope: NodeScope) -> NodeId:
        assert(node_scope.current_node_id is not None)
        return node_scope.current_node_id

    @singleton
    @multiprovider
    def provide_group(
            self, node_scope: NodeScope, node_builder: ClassAssistedBuilder[Node]) -> Group:
        group = Group([])
        for i in range(2):
            node_scope.set_node(NodeId(i))
            group.append(node_builder.build())
        return group


def main():
    injector = Injector(SimpleModule())
    assert(injector.get(EventQueue) is injector.get(EventQueue))
    assert(injector.get(Network) is injector.get(Network))
    assert(injector.get(Group) is injector.get(Group))
    node_scope = injector.get(NodeScope)
    node_id_set = set()
    group = injector.get(Group)
    for node_ in group:
        node_scope.set_node(node_.id)
        node_id_set.add(injector.get(NodeId))
    assert(len(node_id_set) == len(group))
    print(group[0])
    print(group[1])

    simulator = injector.get(Simulator)
    simulator.run()


if __name__ == '__main__':
    main()
