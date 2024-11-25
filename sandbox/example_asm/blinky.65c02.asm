.target "65C02"
.format "TXT" 
.setting "OutputTxtValuesInLine" = 16

; CONSTANTS
PORTB = $6000  ; data bus to the LCD
PORTA = $6001  ; top three bits are LCD control, b4 is LED, b0..b3 = inputs from buttons
DDRB  = $6002
DDRA  = $6003


  .org $8000

reset: ; entry point for all vectors
  ldx #$ff
  txs               ; setup stack pointer

  lda #%11111111    ; Set all pins on port B to output 
  sta DDRB
  lda #%11110000    ; Set top 4 pins on port A to output 
  sta DDRA
  lda #0
  sta PORTB
  sta PORTA

inf_loop:
  lda #%00010000    ; b4 is LED
  sta PORTA
  jsr short_delay
  lda #%00000000    ; b4 is LED
  sta PORTA
  jsr short_delay
  jmp inf_loop

short_delay:
  ldy  #100    ; (2 cycles)
  ldx  #$ff    ; (2 cycles)
_delay:
  dex          ; (2 cycles)
  bne  _delay  ; (3 cycles in loop, 2 cycles at end)
  dey          ; (2 cycles)
  bne  _delay  ; (3 cycles in loop, 2 cycles at end)
  rts

.org  $fffa ;irq vectors (little endian addresses)
.word reset ;NMI @ fffa/b
.word reset ;RST @ fffc/d
.word reset ;IRQ @ fffe/f
  