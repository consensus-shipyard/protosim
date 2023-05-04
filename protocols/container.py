from dependency_injector import containers, providers

from protocols.implementations import BrachaBinaryConsensus, EchoConsistentBroadcast


class Protocols(containers.DeclarativeContainer):
    config = providers.Configuration()
    core = providers.DependenciesContainer()

    bracha_binary_consensus = providers.Factory(
        BrachaBinaryConsensus,
        node_id=core.node_id,
        network=core.network,
        dispatcher=core.dispatcher,
    )

    echo_consistent_broadcast = providers.Factory(
        EchoConsistentBroadcast,
        node_id=core.node_id,
        network=core.network,
        dispatcher=core.dispatcher,
    )

    @classmethod
    def protocol_selector(cls, protocol: str) -> providers.Selector:
        return providers.Selector(
            protocol,
            bracha_binary_consensus=cls.bracha_binary_consensus,
            echo_consistent_broadcast=cls.echo_consistent_broadcast,
        )
    