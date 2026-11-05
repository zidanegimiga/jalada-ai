import threading
import time

from jalada.application.job_runner import background_jobs, work_until


class Jobs:
    def __init__(self, pending: int, fail_first: bool = False) -> None:
        self.pending = pending
        self.fail_first = fail_first
        self.done = 0

    def run_one(self) -> bool:
        if self.fail_first:
            self.fail_first = False
            raise ConnectionError("database unreachable")
        if self.pending == 0:
            return False
        self.pending -= 1
        self.done += 1
        return True


def wait_for(condition: object, seconds: float = 2.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():  # type: ignore[operator]
            return True
        time.sleep(0.01)
    return False


def test_jobs_run_on_a_thread_while_the_block_lasts() -> None:
    jobs = Jobs(pending=3)

    with background_jobs(jobs, poll_interval=0.01):
        assert wait_for(lambda: jobs.done == 3)

    assert not any(t.name == "jobs" for t in threading.enumerate()), "the thread stopped"


def test_a_failure_outside_a_job_does_not_stop_the_loop() -> None:
    jobs = Jobs(pending=1, fail_first=True)
    stop = threading.Event()
    thread = threading.Thread(target=work_until, args=(stop, jobs, 0.01))
    thread.start()

    assert wait_for(lambda: jobs.done == 1)
    stop.set()
    thread.join(timeout=2)
