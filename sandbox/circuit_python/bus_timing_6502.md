# Bus Timing for 65c02 CPU #

## Reset

See section 3.11 of the WDC 65c02 datasheet:
* drive Reset (RESB) line low to put CPU into reset
* delay a few milliseconds settle
* set control lines to reset state
* perform 3 "wake-up" clock cycles
* drive Reset (RESB) line high to bring CPU out of reset
* perform 7 "initialization" clock cycles


## General CPU clock cycle

See section 6.3 of the WDC 65c02 datasheet:
* bring the clock (PHI2) low to start the cycle
* if the previous cycle was a read (need_to_reset_data_bus is True)
  * free DATA bus
* wait tADS (40 ns)
* capture ADDR bus and control lines
* if read (MEM --> CPU)
  * present data to DATA bus
  * raise clock (PHI2)
  * set flag need_to_reset_data_bus to True
* if write (CPU --> MEM)
  * raise clock (PHI2)
  * read DATA bus


