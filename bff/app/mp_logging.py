import logging
import logging.handlers
import multiprocessing
import threading
import queue
import sys

LOG_FILE = "bff.log"
LOG_MAX_BYTES = 2 * 1024 * 1024  # 2 MB per file
LOG_BACKUP_COUNT = 5

def log_listener_process(log_queue, log_file=LOG_FILE):
    """Process that receives log records and writes them to rotating files."""
    root = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s %(processName)s %(threadName)s %(levelname)s %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    while True:
        try:
            record = log_queue.get()
            if record is None:
                break  # Sentinel to shut down
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import traceback
            print("Logging error:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

def get_logger(log_queue, name:str = "BFF"):
    """Return a logger that sends records to the logging queue."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Prevent adding multiple handlers if called repeatedly
    if not any(isinstance(h, logging.handlers.QueueHandler) for h in logger.handlers):
        handler = logging.handlers.QueueHandler(log_queue)
        logger.addHandler(handler)
    return logger

def start_logging_subprocess(log_queue=None, log_file=LOG_FILE):
    """Start the logging subprocess. Returns the queue and process."""
    if log_queue is None:
        log_queue = multiprocessing.Queue(-1)
    proc = multiprocessing.Process(
        target=log_listener_process, args=(log_queue, log_file), daemon=True
    )
    proc.start()
    return log_queue, proc

def stop_logging_subprocess(log_queue, proc):
    """Stop the logging subprocess cleanly."""
    log_queue.put_nowait(None)
    proc.join(timeout=5)

# Example usage:
if __name__ == "__main__":
    log_queue, log_proc = start_logging_subprocess()
    logger: logging.Logger = get_logger(log_queue)
    logger.info("Hello from main process!")
    stop_logging_subprocess(log_queue, log_proc)