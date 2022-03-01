import traceback
import schedule
from threading import Thread, current_thread
import time
from queue import Queue
from logging import getLogger
import threading
import logging

n_workers = 4


class CronQueue:

    logger = None
    db = None
    queue = None
    workers = []
    stop_thread_event = None

    def __init__(self, cron_config, db):
        self.logger = getLogger("CronQueue")
        self.db = db
        self.queue = Queue(0)
        self.cron_config = cron_config

        self.init_workers()
        self.init_schedulers()

    def init_workers(self):
        self.logger.exception("Init workers")
        for _ in range(n_workers):
            self.add_worker()

    def init_schedulers(self):
        self.logger.exception("Init schedulers")

        try:
            for m in self.cron_config:
                if m["cron"].startswith("*"):
                    schedule.every().hour.at(m["cron"][1:]).do(lambda m=m: self.queue.put(m))
                else:
                    schedule.every().day.at(m["cron"]).do(lambda m=m: self.queue.put(m))
        except Exception as err:
            traceback.print_exc()
            self.logger.exception("Exception: %s", err)

    def add_worker(self):
        w = Thread(target=self.work)
        w.start()
        self.workers.append(w)

    def work(self):
        self.logger.warning("%s worker initialized", current_thread().name)

        try:
            while True:
                cron_description = self.queue.get()
                self.execute_cron(cron_description)
        except Exception as err:
            traceback.print_exc()
            self.logger.exception("Exception : %s", err)
        finally:
            self.logger.warning("%s: Exiting", {current_thread().name})

    def execute_cron(self, cron_description):
        start = time.time()
        self.logger.warning("%s cron %s", current_thread().name, cron_description['class'].__name__)

        my_instance = cron_description["class"](**cron_description["config"])
        my_instance.run(self.db)
        del my_instance

        end = time.time()
        self.logger.warning("%s done", cron_description['class'].__name__)
        self.logger.warning("Completed in : %s", str(end-start))

    def run_queue(self, interval=1):
        """Continuously run, while executing pending jobs at each elapsed
        time interval.
        Please note that it is *intended behavior that run_continuously()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you set a continuous run interval
        of one hour then your job won't be run 60 times at each interval but
        only once.
        IMPORTED FROM https://github.com/mrhwick/schedule
        """
        self.stop_thread_event = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not self.stop_thread_event.is_set():
                    schedule.run_pending()
                    self.stop_thread_event.wait(timeout=interval)
                logger = logging.getLogger()
                logger.warning("Exiting Scheduling")

        continuous_thread = ScheduleThread()
        continuous_thread.start()

    def stop_queue(self):
        self.stop_thread_event.set()
