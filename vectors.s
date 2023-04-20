/*
* Copyright 2019 ETH Zürich and University of Bologna
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

.section .vectors, "ax"
.option norvc
vector_table:
	j sw_irq_handler         /* 0 */
	j __no_irq_handler       /* 1 */
	j __no_irq_handler       /* 2 */
	j software_irq_handler   /* 3 */
	j __no_irq_handler       /* 4 */
	j __no_irq_handler       /* 5 */
	j __no_irq_handler       /* 6 */
	j timer_irq_handler      /* 7 */
	j __no_irq_handler       /* 8 */
	j __no_irq_handler       /* 9 */
	j __no_irq_handler       /* 10 */
	j external_irq_handler   /* 11 */
	j __no_irq_handler       /* 12 */
	j __no_irq_handler       /* 13 */
	j __no_irq_handler       /* 14 */
	j __no_irq_handler       /* 15 */
	j __no_irq_handler       /* 16 */
	j __no_irq_handler       /* 17 */
	j __no_irq_handler       /* 18 */
	j __no_irq_handler       /* 19 */
	j __no_irq_handler       /* 20 */
	j __no_irq_handler       /* 21 */
	j __no_irq_handler       /* 22 */
	j __no_irq_handler       /* 23 */
	j __no_irq_handler       /* 24 */
	j __no_irq_handler       /* 25 */
	j __no_irq_handler       /* 26 */
	j __no_irq_handler       /* 27 */
	j __no_irq_handler       /* 28 */
	j __no_irq_handler       /* 29 */
	j __no_irq_handler       /* 30 */
	j __no_irq_handler       /* 31 */

.section .text.vecs
/* exception handling */
__no_irq_handler:
	la a0, no_exception_handler_msg
	jal ra, puts
	j __no_irq_handler


sw_irq_handler:
	csrr t0, mcause
	slli t0, t0, 1  /* shift off the high bit */
	srli t0, t0, 1
	li t1, 2
	beq t0, t1, handle_illegal_insn
	li t1, 11
	beq t0, t1, handle_ecall
	li t1, 3
	beq t0, t1, handle_ebreak
	j handle_unknown

handle_ecall:
	la a0, ecall_msg
	jal ra, puts
	j end_handler

handle_ebreak:
	la a0, ebreak_msg
	jal ra, puts
	j end_handler

handle_illegal_insn:
	la a0, illegal_insn_msg
	jal ra, puts
	j end_handler

handle_unknown:
	la a0, unknown_msg
	jal ra, puts
	j end_handler

end_handler:
	csrr a0, mepc
	addi a0, a0, 4
	csrw mepc, a0
	mret
/* this interrupt can be generated for verification purposes, random or when the PC is equal to a given value*/
verification_irq_handler:
	mret

software_irq_handler:
	la a0, software_irq_msg
	jal ra, puts
	mret

timer_irq_handler:
	la a0, timer_irq_msg
	jal ra, puts
	mret

external_irq_handler:
	la a0, external_irq_msg
	jal ra, puts
	mret


.section .rodata
illegal_insn_msg:
	.string "illegal instruction exception handler entered\n"
ecall_msg:
	.string "ecall exception handler entered\n"
ebreak_msg:
	.string "ebreak exception handler entered\n"
unknown_msg:
	.string "unknown exception handler entered\n"
no_exception_handler_msg:
	.string "no exception handler installed\n"
software_irq_msg:
	.string "software irq handler entered\n"
timer_irq_msg:
	.string "timer irq handler entered\n"
external_irq_msg:
	.string "external irq handler entered\n"
