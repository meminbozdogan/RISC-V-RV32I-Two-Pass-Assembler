addi x2, x0, 1024
addi x1, x0, 1
addi x9, x0, 64

sola_kaydir:
sw x1, 0(x2)
lui x3, 1220

gecikme_sola:
addi x3, x3, -1
bne x3, x0, gecikme_sola
slli x1, x1, 1
blt x1, x9, sola_kaydir

saga_kaydir:
srli x1, x1, 1
sw x1, 0(x2)
lui x3, 1220

gecikme_saga:
addi x3, x3, -1
bne x3, x0, gecikme_saga
bne x1, x0, saga_kaydir

addi x1, x0, 1
jal x0, sola_kaydir