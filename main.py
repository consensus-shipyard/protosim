import dataclasses
import inspect
from typing import Annotated, Callable, Any, Generic, TypeVar

from core import EventQueue, Network, Dispatcher, NodeId, InstanceId, Node, Simulator
from protocols.implementations import EchoConsistentBroadcast, BrachaBinaryConsensus, ProtocolFactory

@dataclasses.dataclass
class A:
    name: Annotated[str, "for_A"]

# Scopes
singleton = "singleton"
factory = "factory"

T = TypeVar("T")
class Factory(Generic[T]):
    def __init__(self, underlying_type, **kwargs):
        self.underlying_type = underlying_type
        self._default_args = kwargs

    def create(self, **kwargs):
        return self.underlying_type(**(self._default_args | kwargs))

# Container
class Container:
    def __init__(self):
        self.bindings: dict[type, Callable[..., Any]] = {}
        self.singletons: dict[type, Any] = {}

    @staticmethod
    def get_annotations_of_callable(callable_obj: Callable[..., Any]) -> dict:
        signature = inspect.signature(callable_obj)
        return dict(signature.parameters)

    @staticmethod
    def get_annotations_of_dataclass(dataclass_type: type) -> dict:
        annotations = {}
        for field in dataclasses.fields(dataclass_type):
            if field.default and field.default_factory is dataclasses.MISSING:
                annotations[field.name] = field.type
        return annotations

    def _construct_dataclass(self, dataclass_type: type):
        annotations = self.get_annotations_of_dataclass(dataclass_type)
        kwargs = {}
        for param_name, param_type in annotations.items():
            param_instance = self.get(param_type)
            kwargs[param_name] = param_instance
        return dataclass_type(**kwargs)

    def _construct_factory(self, dataclass_type: type):
        print(dataclass_type)
        annotations = self.get_annotations_of_dataclass(dataclass_type)
        default_args = {}
        for param_name, param_type in annotations.items():
            try:
                param_instance = self.get(param_type)
                default_args[param_name] = param_instance
            except Exception:  # TODO: Be more specific
                # We simply don't add this parameter to the factory and instead except it to be passed by the user.
                pass
        return Factory[dataclass_type](dataclass_type, **default_args)

    def get(self, object_type: type | str):
        # If the object type is a string, we need to convert it to a type
        if type(object_type) is str:
            object_type = globals()[object_type]

        # Check if the object is present in the singleton context
        if object_type in self.singletons:
            return self.singletons[object_type]

        # Act according to the type of the object
        if dataclasses.is_dataclass(object_type):
            instance = self._construct_dataclass(object_type)
            self.singletons[object_type] = instance
            return instance
        elif object_type.__origin__ is Factory:
            underlying_type = object_type.__args__[0]
            assert(dataclasses.is_dataclass(underlying_type))
            # TODO: What is the scope of a factory?
            return self._construct_factory(underlying_type)
        else:
            raise ValueError(f"Unsupported type {object_type}. Only @dataclass and Factory of @dataclass are supported.")


def wire_manually():
    group_size = 4
    root_type = BrachaBinaryConsensus
    broadcast_type = EchoConsistentBroadcast

    event_queue = EventQueue()
    network = Network(event_queue)

    root_instance_id = InstanceId(("root", 0))

    group = []
    for i in range(group_size):
        node_id = NodeId(i)
        dispatcher = Dispatcher(node_id)

        root_factory = ProtocolFactory(root_type, node_id, network, dispatcher)
        broadcast_factory = ProtocolFactory(broadcast_type, node_id, network, dispatcher)
        root_protocol = root_factory.create(root_instance_id, value=True, broadcast_factory=broadcast_factory)

        node = Node(node_id, root_protocol, dispatcher)
        group.append(node)
        print(node)
        print()

    sim = Simulator(group, event_queue, network)
    return sim


if __name__ == "__main__":
    simulator = wire_manually()
    simulator.run()

# Ignore the code below for now
if False:
    container = Container()
    #container.get(Factory[A])

    event_queue = container.get(EventQueue)
    print(event_queue)

    network = container.get(Network)
    print(network)

    network_factory = container.get(Factory[Network])
    print(network_factory.create())
    #container.bind_instance(NodeId, NodeId(0))
    #dispatcher = container.get(Dispatcher)
    #print(dispatcher)
    #a = build_object(A)





