function jump_to(target : xlenbits) -> ExecutionResult = {
    set_next_pc(target);
    RETIRE_SUCCESS
}
