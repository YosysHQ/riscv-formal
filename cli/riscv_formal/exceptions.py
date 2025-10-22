from pathlib import Path

class BadExtensionError(Exception):
    extension: Path

    def __init__(self, extension: Path, *args: object) -> None:
        super().__init__(*args)
        self.extension = extension

    def __str__(self) -> str:
        return f"'{self.extension}' must be a valid python script/module"

class LoadingExtensionError(BadExtensionError):
    def __str__(self) -> str:
        if self.__cause__ is None:
            err_str = "Encountered exception"
        else:
            err_str = f"Encountered {type(self.__cause__).__name__!r}"
        if self.extension:
            err_str += f" while loading '{self.extension}'"
        cause_str = str(self.__cause__)
        if cause_str:
            err_str += f": {cause_str}"
        return err_str
