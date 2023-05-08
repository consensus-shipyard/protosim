import inspect
from dataclasses import dataclass
import logging
from typing import Any, Optional, Callable, Type, get_type_hints

from core import NodeId
from injection import Factory, Scope


# A sentinel type to detect whether an instance is supplied.
class _ABSENT:
    def __str__(self):
        return "ABSENT"

    def __repr__(self):
        return str(self)


ABSENT = _ABSENT()


# A binding from a type to a constructor and a scope.
@dataclass
class Binding:
    object_type: Type
    constructor: Optional[Callable[..., Any]]
    scope: Scope
    instance: Any = ABSENT


class Injector:
    def __init__(self):
        self._bindings_by_type: dict[Type, Binding] = {
            Injector: Binding(Injector, constructor=lambda: self,
                              scope=Scope.SINGLETON, instance=self)
        }
        self._bindings_with_node_scope: list[Binding] = []
        self._current_node_scope: Optional[NodeId] = None

    def provide(
            self, object_type: Type,
            constructor: Optional[Callable[..., Any]] = None,
            scope: Scope = Scope.UNSCOPED) -> None:
        if object_type in self._bindings_by_type:
            raise Exception(
                f"Type {object_type} already has a binding: {self._bindings_by_type[object_type]}.")

        if constructor is None:
            constructor = object_type

        binding = Binding(object_type, constructor, scope)
        self._bindings_by_type[object_type] = binding
        if scope == Scope.NODE:
            self._bindings_with_node_scope.append(binding)

    def supply(self, object_type: Type, instance: Any):
        if object_type in self._bindings_by_type:
            raise Exception(
                f"Type {object_type} already has a binding: {self._bindings_by_type[object_type]}.")
        self._bindings_by_type[object_type] = Binding(object_type, None,
                                                      Scope.SINGLETON, instance)

    def _resolve_constructor(self, object_type: Type) -> Callable[..., Any]:
        logging.debug(f"Resolving constructor for {object_type}")
        binding = self._bindings_by_type.get(object_type, None)

        if binding:
            logging.debug(f"Found binding: {object_type} -> {binding}.")
            if binding.scope is Scope.NODE and self._current_node_scope is None:
                raise Exception(
                    f"Cannot get an object with a node-scoped binding outside of a node scope")

            if binding.instance is not ABSENT:
                logging.debug(f"Binding has an instance: {binding.instance}.")
                return lambda: binding.instance

            logging.debug(
                f"Binding has no instance, returning constructor: {binding.constructor}")
            return binding.constructor

        logging.debug(
            f"No binding found for {object_type}. Using the type itself as a constructor")
        return object_type

    def _resolve_parameters(self, constructor: Callable[..., Any],
                            strict=True) -> dict[str, Any]:
        signature = inspect.signature(constructor)
        logging.debug(
            f"Resolving parameters for constructor {constructor} with signature {signature}")

        # Resolve the constructor's parameters
        constructor_arguments = {}
        for parameter in signature.parameters.values():
            if parameter.annotation is inspect.Parameter.empty:
                raise Exception(
                    f"Cannot construct an object with an unannotated parameter: {parameter.name}")
            logging.debug(
                f"{parameter.annotation}, {type(parameter.annotation)}")
            parameter_type = parameter.annotation
            if type(parameter_type) is str:
                parameter_type = \
                    get_type_hints(constructor, include_extras=True)[parameter.name]

            # We can only inject parameters that have a binding or a default value
            if strict and parameter_type not in self._bindings_by_type and parameter.default is inspect.Parameter.empty:
                logging.debug(
                    f"{parameter.annotation}, {type(parameter.annotation)}")
                logging.debug(
                    f"Cannot inject parameter {parameter.name} of type {parameter_type}. " +
                    "It has no binding and no default value.")
                raise Exception(
                    f"Cannot inject object of type {parameter_type} for constructor with signature {signature}. " +
                    "It needs either a binding in the injector or a default value in the constructor.")

            # We inject the parameter if it has a binding or if it has no default value
            if parameter_type in self._bindings_by_type or parameter.default is inspect.Parameter.empty:
                parameter_value = self.get(parameter_type)
                constructor_arguments[parameter.name] = parameter_value

        logging.debug(
            f"Resolved constructor arguments: {constructor_arguments}.")
        return constructor_arguments

    def _construct_instance(self, constructor: Callable[..., Any]) -> Any:
        constructor_arguments = self._resolve_parameters(constructor)
        return constructor(**constructor_arguments)

    def _construct_factory(self, constructor: Callable[..., Any]) -> Any:
        signature = inspect.signature(constructor)
        return_type = signature.return_annotation
        assert (return_type is not inspect.Parameter.empty)
        default_args = self._resolve_parameters(constructor, strict=False)
        return Factory[return_type](constructor, default_args)

    def _save_instance(self, object_type: Type, instance: Any) -> None:
        binding = self._bindings_by_type.get(object_type, None)

        if binding and binding.scope is not Scope.UNSCOPED:
            if binding.scope is Scope.NODE:
                assert self._current_node_scope is not None, "Cannot save a node-scoped object outside of a node"
                self._bindings_with_node_scope.append(binding)
            binding.instance = instance

    def get(self, object_type: Type) -> Any:
        logging.debug(f"Calling Injector#get for object type {object_type}")
        if hasattr(object_type, '__origin__') and object_type.__origin__ is Factory:
            underlying_type = object_type.__args__[0]
            constructor = self._resolve_constructor(underlying_type)
            factory = self._construct_factory(constructor)
            logging.debug(f"Constructed factory: {factory}")
            return factory
        else:
            constructor = self._resolve_constructor(object_type)
            instance = self._construct_instance(constructor)
            logging.debug(f"Constructed instance: {instance}")
            self._save_instance(object_type, instance)
            return instance

    def enter_node_scope(self, node_id: NodeId) -> None:
        self._current_node_scope = node_id
        if NodeId not in self._bindings_by_type:
            self.provide(NodeId, lambda: self._current_node_scope, Scope.NODE)

    def exit_node_scope(self) -> None:
        self._current_node_scope = None
        for binding in self._bindings_with_node_scope:
            binding.instance = ABSENT
