from __future__ import annotations

import io
import traceback

import yosys_mau.task_loop.job_server as job
from yosys_mau import task_loop as tl

from riscv_formal.config import arg_parser, App, parse_config


def main() -> None:
    args = arg_parser().parse_args()

    job.global_client(args.jobs)

    # Move command line arguments into the App context
    for name in dir(args):
        if name in type(App).__mro__[1].__annotations__:
            setattr(App, name, getattr(args, name))

    App.raw_args = args

    try:
        tl.run_task_loop(task_loop_main)
    except tl.TaskCancelled:
        exit(1)
    except BaseException as e:
        if App.debug or App.debug_events:
            traceback.print_exc()
        tl.log_exception(e, raise_error=False)  # Automatically avoids double logging
        exit(1)


async def task_loop_main() -> None:
    early_log = setup_logging()
    parse_config()
    tl.log("running command", App.command)

    match App.command:
        case "setup":
            await SetupTask().finished
        case _:
            raise NotImplementedError()

    tl.log("finished")


class SetupTask(tl.Task):
    async def on_prepare(self) -> None:
        tl.LogContext.scope = "setup"

    async def on_run(self):
        for option in App.config.options.options():
            tl.log("option", option.name, repr(getattr(App.config.options, option.name)))

        for define_type, defines in [
            ("hdl defines", App.config.defines),
            ("script defines", App.config.script_defines),
            ("script sources", App.config.script_sources),
            ("script links", App.config.script_links),
        ]:
            for check_name, check_defines in defines.items():
                if check_name:
                    tl.log(f"got {define_type} for check {check_name}")
                else:
                    tl.log(f"got default {define_type}")
                tl.log_debug(check_defines)

        for file_type, files in [
            ("verilog", App.config.verilog_files),
            ("vhdl", App.config.vhdl_files),
        ]:
            tl.log(f"got {file_type} files")
            for file in files:
                tl.log_debug(file)

        for check_name, defines in App.config.script_defines.items():
            if check_name:
                tl.log(f"got defines for check {check_name}")
            else:
                tl.log(f"got default defines")
            tl.log_debug(defines)

        for unhandled_section in App.config.unhandled:
            tl.log("unhandled section", unhandled_section.header)


def setup_logging() -> io.StringIO:
    tl.LogContext.app_name = "RVF"
    tl.logging.start_logging()
    early_log = io.StringIO()
    tl.logging.start_logging(early_log)

    if App.debug_events:
        tl.logging.start_debug_event_logging()
    if App.debug:
        tl.LogContext.level = "debug"

    def error_handler(err: BaseException):
        if isinstance(err, tl.TaskCancelled):
            return
        tl.log_exception(err, raise_error=True)

    tl.current_task().set_error_handler(None, error_handler)
    return early_log


if __name__ == "__main__":
    main()
