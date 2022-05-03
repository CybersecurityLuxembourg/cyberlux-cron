# pylint: disable=unused-import
# flake8: noqa: F401
import inspect
import sys
from resource.front_app import FrontApp
from resource.engine.add_worker import AddWorker
from resource.engine.get_thread_count import GetThreadCount
from resource.engine.get_worker_count import GetWorkerCount


def set_routes(*args):

    plugins = args[0]

    # Create the root endpoint

    plugins["api"].add_resource(
        FrontApp,
        "/",
        resource_class_kwargs={"db": plugins["db"], "engine": plugins["engine"]}
    )

    # Build the endpoints imported in this file

    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    classes = [c for c in classes if c[0] != "FrontApp"]

    for res in classes:

        # Build the endpoint

        endpoint = res[1].__module__.replace("resource.", ".", 1).replace(".", "/")

        functions = inspect.getmembers(res[1], predicate=inspect.isfunction)
        http_functions = [f for n, f in functions if n in ["get", "post"]]

        if len(http_functions) == 0:
            raise Exception(f"No http function found on resource {res[1].__module__}")
        if len(http_functions) > 1:
            raise Exception(f"Too much http functions found on resource {res[1].__module__}")

        function_args = [a for a in inspect.signature(http_functions[0]).parameters if a != "self" and a != "kwargs"]

        if len(function_args) > 1:
            raise Exception(f"Too much args for http function on resource {res[1].__module__}")

        if len(function_args) == 1:
            endpoint += f"/<{function_args[0]}>"

        # Build the args

        class_args = {a: plugins[a] for a in inspect.getfullargspec(res[1]).args if a != "self"}
        print(class_args)

        # Add the resource

        plugins["api"].add_resource(res[1], endpoint, resource_class_kwargs=class_args)

        # Add the resource in the doc
        print(res)
        plugins["docs"].register(res[1], resource_class_kwargs=class_args)
