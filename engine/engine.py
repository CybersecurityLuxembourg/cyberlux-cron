import traceback
from engine.cron_queue import CronQueue
import threading
from queue import Queue
from logging import getLogger
import json
import sys
import importlib


class Engine:

    logger = None
    queue = None
    cron_queue = None
    cron_config = None
    db = None

    def __init__(self, db):
        self.logger = getLogger("Engine")
        self.db = db
        self.load_cron_config()

    def load_cron_config(self):
        f = open("config/cron_config.json", "r")
        cron_config = f.read()
        cron_config = json.loads(cron_config)

        self.logger.warning("Loading cron config: %s found", {len(cron_config)})

        for c in cron_config:
            if "class" not in c:
                raise Exception("No class defined for cron in config")

            try:
                class_name = c["class"].split(".")[-1]
                package_name = (".".join(c["class"].split(".")[0:-1]))
                if package_name not in sys.modules:
                    package = importlib.import_module(package_name)
                else:
                    package = importlib.reload(importlib.import_module(package_name))
                c["class"] = getattr(package, class_name)
            except Exception:
                raise Exception(f"Class not found on config loading: {c['class']}")

        self.cron_config = cron_config

    def run(self):
        self.logger.warning("Start engine")

        try:
            self.queue = Queue(0)
            self.cron_queue = CronQueue(self.cron_config, self.db)
            self.cron_queue.run_queue()

            while self.execute_command():
                pass

        except Exception as err:
            traceback.print_exc(err)
        finally:
            self.cron_queue.stop_queue()

            while not self.queue.empty:
                self.queue.get_nowait()

            self.logger.warning("Stop engine")

    def execute_command(self):
        queue, command = self.queue.get()
        self.logger.warning("Execute command: %s", command)

        for w in self.cron_queue.workers:
            if not w.isAlive():
                self.cron_queue.workers.remove(w)

        if command == "ADD_WORKER":
            self.cron_queue.add_worker()
        elif command == "GET_NUMBER_OF_THREAD":
            queue.put(threading.active_count())
        elif command == "GET_NUMBER_OF_WORKERS":
            queue.put(len(self.cron_queue.workers))
        elif command == "STOP":
            return False
        return True
