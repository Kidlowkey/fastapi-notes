"""
Background Worker.
On Render this maps 1:1 to a "Background Worker" service: it runs
continuously, never receives inbound HTTP traffic, and just polls a
queue (here: a Redis list) for work. Its start command would simply be:

    python worker.py

It initiates outbound connections (to Redis, to an email API, etc.)
but nothing can ever call *it* directly.
"""

import json
import signal
import sys
import time

import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
QUEUE_NAME = "render_demo_queue"
RESULTS_HASH = "render_demo_results"

running = True


def handle_sigterm(signum, frame):
    """
    Render sends SIGTERM on deploys/restarts. Handling it lets you
    finish (or cleanly abandon) the job you're mid-way through instead
    of getting killed mid-task. Render also lets you extend the grace
    period via maxShutdownDelaySeconds for slower jobs.
    """
    global running
    print("[worker] received SIGTERM, shutting down after current job...", flush=True)
    running = False


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)


def process_job(job: dict):
    print(
        f"[worker] picked up job {job['id']} -> {job['type']} for {job['email']}",
        flush=True,
    )
    # Simulate slow work: sending an email, calling an API, crunching data...
    time.sleep(2)
    result = {
        "id": job["id"],
        "status": "completed",
        "email": job["email"],
        "completed_at": time.time(),
    }
    r.hset(RESULTS_HASH, job["id"], json.dumps(result))
    print(f"[worker] finished job {job['id']}", flush=True)


def main():
    print("[worker] started, polling queue:", QUEUE_NAME, flush=True)
    while running:
        # BLPOP blocks (up to timeout) instead of busy-looping —
        # this is the "event loop listening on a queue" pattern.
        item = r.blpop(QUEUE_NAME, timeout=2)
        if item is None:
            continue  # nothing to do, loop back and check `running`
        _, raw_job = item
        job = json.loads(raw_job)
        process_job(job)
    print("[worker] stopped cleanly.", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
