from types import SimpleNamespace


class InstanceId(SimpleNamespace):
    pass


class Path(tuple[InstanceId, ...]):
    def append(self, instance_id: InstanceId):
        return self + (instance_id,)


if __name__ == "__main__":

    instanceId = InstanceId(id=1, round=1, step=2)
    print(instanceId)

    path = Path()
    print(path.append(instanceId))
