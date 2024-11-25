.target "65C02"

; SETTING:                    TYPE:   DEFAULT:   DESCRIPTION:
; --------------------------- ------- ---------- ------------
; OutputTxtAddressFormatFirst String  "{0:x04} " String formatting for the memory address in the first line of a new area. Example: "8fc0 " (with space). {0:X04} with uppercase X would make it print an uppercase hexadecimal number.
; OutputTxtAddressFormatNext  String  "{0:x04} " String formatting for the memory address in subsequent lines of the area, in case you want to drop the address display there. Example: "8fc0 " (with space)
; OutputTxtValueFormat	      String  "{0:x02}"  String formatting for each displayed byte value. Example: "7f" {0:X02} with uppercase X would make it print an uppercase hexadecimal number.
; OutputTxtValueSeparator	  String  " "        Separator placed between each displayed byte value in a line of text.	
; OutputTxtAreaSeparator	  String  "\r\n"     Separator placed between each area. Areas are continuous bytes, if there is a gap in the memory, a new area opens.
; OutputTxtLineSeparator	  String  "\r\n"     Separator placed between each displayed line. It's basically the newline character of your choice.
; OutputTxtValuesInLine       Integer 8          The maximum number of displayed byte values in each line.	8

; .setting "<name>" = <value> (use quotes for strings)
.setting "OutputTxtValuesInLine" = 16

.org $ff00

.memory "fill", $ff00, $0100, $ea

reset:
    ; set stack pointer
    ldx #$ff
    txs 

    ldx #0
printloop:
    lda message,x
    beq resetc
    jsr print_char
    inx
    jmp printloop

message: .asciiz "Hello, World!\r\n"

print_char:
    sta OUTPUT_REG
    rts

.org $fff0
 OUTPUT_REG .byte 0

.org  $fffa ;irq vectors (little endian addresses)
.word reset ;NMI @ fffa/b
.word reset ;RST @ fffc/d
.word reset ;IRQ @ fffe/f