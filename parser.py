import argparse
import importlib
import inspect

from injection.injector import AbstractModule


def is_module(obj):
    return inspect.isclass(obj) and inspect.getmodule(obj) is mod and issubclass(obj, AbstractModule)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("modules", nargs='+', type=str, default="ping", help="whitespace-separated list of modules")
    parser.add_argument("-g", "--group-size", type=int, default=4, help="number of nodes in the group")
    args = parser.parse_args()


    def is_module(obj):
        return inspect.isclass(obj) and inspect.getmodule(obj) is mod and issubclass(obj, AbstractModule)

    for module_name in args.modules:
        print(module_name)
        mod = importlib.import_module(f"modules.{module_name}")
        injector_modules = [module_cls[1] for module_cls in inspect.getmembers(mod, is_module)]

