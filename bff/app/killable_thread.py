"""In general, base implementation of a thread in Python does not provide any posibility to abruptly kill a thread.
    
But you might want to "kill" a thread when certain time is elapsed or some critical conditions are met.
KillableThread provides an additional method called `kill` that gives you the opertunity to cancel the execution upon the next line of code.

**Be aware that killing a thread might leave critical resources taht might be closed properly, open.**

If you want some action to be executed when the Thread is going to be killed, plese provide an `on_kill` handler. 
Do not provide an `on_kill` handler if no action is required.

:Example:
    ```
    def runner():
        while True:
            print(time.time())
            time.sleep(1)
        
    def on_kill():
        print("killing")
    
    th = KillableThread(target=runner, on_kill=on_kill)
    # th = KillableThread(target=runner)
    th.start()
    time.sleep(2)
    th.kill()
    th.join()
    ```

* Current implementation was inspired by this post (https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/)
"""
    
from __future__ import annotations
import sys
import threading
from typing import Callable, Iterable, Mapping, Any, List


class KillableThread(threading.Thread):
    """A thread class that supports being killed and paused.
    This class extends the standard `threading.Thread` class to add functionality
    for pausing and killing the thread. When a thread is killed, it will stop
    execution before executing the next line of code. When a thread is paused,
    it will wait until it is resumed.
    Attributes:
        on_kill (Callable | None): Optional callback to be executed when the thread is killed.
    Methods:
        start(): Starts the thread.
        kill(): Requests the thread to be killed.
        pause(): Pauses the thread.
        resume(): Resumes the thread if it is paused.
        is_paused(): Returns whether the thread is currently paused.
    """
    def __init__(self, 
                 target: Callable[..., object] | None = None, 
                 on_kill: Callable|None = None,
                 name: str | None = None,
                 group: None = None, 
                 *args, **kwargs):
        super().__init__(group, target, name, *args, **kwargs, daemon=True)
        self.__killed__:bool = False
        self.__paused__:bool = False
        self.__resume_event__ = threading.Event()
        self.on_kill:Callable|None = on_kill
        
    def __run__(self):
        sys.settrace(self.__globaltrace__)
        self.__run_backup__()
        self.run = self.__run_backup__
        
    def __globaltrace__(self, frame, event, arg):
        if event == "call":
            return self.__localtrace__
        return None
    
    def __localtrace__(self, frame, event, arg):
        if self.__killed__:
            if event == "line":
                if self.on_kill is not None:
                    self.on_kill()
                raise SystemExit()
        if self.__paused__:
            self.__resume_event__.wait()
        return self.__localtrace__
    
    def start(self) -> None:
        self.__run_backup__ = self.run
        self.run = self.__run__
        threading.Thread.start(self)
    
    def kill(self):
        """Requests the thread to be killed. The Thread will stop execution before executing next line of code."""
        self.__resume_event__.set() # in case thread is paused
        self.__killed__ = True
        
    def pause(self):
        """Pauses the execution of the threads activity before the next line."""
        
        self.__resume_event__.clear()
        self.__paused__ = True
        
    def resume(self):
        """Continuues the execution of the thread right there where it was paused."""
        self.__resume_event__.set()
        self.__paused__ = False
        
    @property
    def is_paused(self) -> bool:
        """Check if the thread is currently paused.
        Returns:
            bool: True if the thread is paused, False otherwise.
        """

        return self.__paused__