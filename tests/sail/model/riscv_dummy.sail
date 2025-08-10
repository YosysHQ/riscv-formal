val handle_illegal : unit -> unit
function handle_illegal() = ()

val xreg_full_write_callback : (string, regidx, xlenbits) -> unit
function xreg_full_write_callback(_) = ()

union ExecutionResult = {
    Retire_Success : unit,
    Illegal_Instruction : unit,
}
let RETIRE_SUCCESS : ExecutionResult = Retire_Success()

scattered enum extension

val extensionName : extension <-> string
scattered mapping extensionName

val hartSupports : extension -> bool
scattered function hartSupports

val currentlyEnabled : extension -> bool
scattered function currentlyEnabled

enum clause extension = Ext_I
mapping clause extensionName = Ext_I <-> "i"
