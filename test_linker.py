import traceback
from assembler import assemble
from linker import link

main_asm = """
.extern yardimci_fonk
.global MAIN_DEVAM

.data
hedef: .word 0

.text
START:
addi x1, x0, 5
addi x2, x0, 15
jal x3, yardimci_fonk

MAIN_DEVAM:
sw x1, 0(x0)
""".splitlines()

yardimci_asm = """
.global yardimci_fonk
.extern MAIN_DEVAM

.text
yardimci_fonk:
sub x1, x2, x1
jal x0, MAIN_DEVAM
""".splitlines()

try:
    obj_main = assemble(main_asm)
    obj_yardimci = assemble(yardimci_asm)
    merged_text, merged_data, global_symbol_table = link([obj_main, obj_yardimci])
    
    print("SUCCESS")
    print("TEXT SEGMENT:", len(merged_text), "komut")
    print("DATA SEGMENT:", len(merged_data), "veri")
    print("GLOBAL SYMBOLS:", global_symbol_table)
    
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
