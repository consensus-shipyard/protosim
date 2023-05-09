import argparse
import importlib
import inspect
import logging
from typing import Annotated

from core import EventQueue, Network, Dispatcher, NodeId, Node, Simulator, Group
from injection import Injector, Scope
from injection.injector import AbstractModule


class MainModule(AbstractModule):
    # Constructor for the Group of Nodes.
    @staticmethod
    def build_nodes(injector: Injector, group: Group) -> list[Node]:
        nodes = []
        for node_id in group:
            injector.enter_node_scope(node_id)
            nodes.append(injector.get(Node))
            injector.exit_node_scope()
        return nodes

    # Constructor for the Group (list of NodeIds).
    @staticmethod
    def provide_node_ids(group_size: Annotated[int, 'group_size']) -> Group:
        return Group([NodeId(i) for i in range(group_size)])

    # Module configuration.
    def configure(self, injector: Injector):
        injector.provide(EventQueue, scope=Scope.SINGLETON)
        injector.provide(Network, scope=Scope.SINGLETON)
        injector.provide(Dispatcher, scope=Scope.NODE)

        injector.supply(Annotated[int, 'group_size'], self.args.group_size)
        injector.provide(Group, constructor=self.provide_node_ids, scope=Scope.SINGLETON)
        injector.provide(list[Node], constructor=self.build_nodes, scope=Scope.SINGLETON)

        injector.provide(Simulator, constructor=Simulator, scope=Scope.SINGLETON)


# Main function. Sets up the injector and runs the simulator.
def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("modules", nargs='+', type=str, help="whitespace-separated list of modules")
    parser.add_argument("-g", "--group-size", type=int, default=4, help="number of nodes in the group")
    args = parser.parse_args()

    def is_injector_module(obj):
        return inspect.isclass(obj) and inspect.getmodule(obj) is mod and issubclass(obj, AbstractModule)

    injector_modules = [MainModule]
    for module_name in args.modules:
        mod = importlib.import_module(f"modules.{module_name}")
        injector_modules += [module_cls[1] for module_cls in inspect.getmembers(mod, is_injector_module)]

    logging.info(f"Installing modules: {[m.__name__ for m in injector_modules]}")

    injector = Injector(args, injector_modules)
    simulator = injector.get(Simulator)
    simulator.run()


if __name__ == "__main__":
    main()
