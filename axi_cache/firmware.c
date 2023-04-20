/*
 *  NERV -- Naive Educational RISC-V Processor
 *
 *  Copyright (C) 2020  Claire Xenia Wolf <claire@yosyshq.com>
 *
 *  Permission to use, copy, modify, and/or distribute this software for any
 *  purpose with or without fee is hereby granted, provided that the above
 *  copyright notice and this permission notice appear in all copies.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 *  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 *  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 *  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 *  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 *  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 *  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */

void putc(int c)
{
	volatile char *p = (void*)0x02000000;
	*p = c;
}

void do_exit()
{
	volatile unsigned *p = (void*)0x02000000;
	*p = 0x100;
}

void puts(char *s)
{
	while (*s) putc(*(s++));
}


#define SIEVE_SIZE 128

void print_num(unsigned p)
{
	char force = 0;
	char c;
	c = '0';
	while (p >= 100)
		p -= 100, c++;
	if (c != '0' || force)
		putc(c), force = 1;
	c = '0';
	while (p >= 10)
		p -= 10, c++;
	if (c != '0' || force)
		putc(c), force = 1;
	putc('0' + p);
	putc('\n');
}

int main()
{
	char sieve[SIEVE_SIZE];

	puts("Some Primes:\n");
    for (unsigned i = 2; i < SIEVE_SIZE; i++)
		sieve[i] = 1;

    for (unsigned p = 2, p2 = 4; p < SIEVE_SIZE; p += 1, p2 += (p << 1) - 1) {
        if (sieve[p]) {
			print_num(p);
			if (p2 < SIEVE_SIZE) {
				for (unsigned i = p2; i < SIEVE_SIZE; i += p) {
					sieve[i] = 0;
				}
			}
        }
    }

	do_exit();
	return 0;
}
