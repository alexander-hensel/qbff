from collections.abc import Callable

class Exceptions:
    class ViewAlreadyRegistered(Exception):
        def __init__(self, view_name:str) -> None:
            super().__init__(f"A View with the name '{view_name}' is already registered")

    class BackgroundTaskAlreadyDefined(Exception):
        def __init__(self, function:Callable) -> None:
            super().__init__(f"A Task with the name '{function.__name__}' is already registered")
    
    class MeasurementTaskAlreadyDefined(BackgroundTaskAlreadyDefined):
        ...

    class MeasurementAlreadyRunning(Exception):
        def __init__(self, functions:list[str]) -> None:
            functions_str = ", ".join(functions)
            super().__init__(f"Following functions are still running: {functions_str}")