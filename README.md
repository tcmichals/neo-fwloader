# neo-fwloader
python script to load M4 firmware.  Supports binary and Intel HEX files

To load SRAM TCML (Reset vector has 32K of SRAM) SRAM, OCRAM memory and DDR memory.

For example:
FreeRTOS, interrupts, drivers should be under 32K, so map it to TCML
User App and other code:  DRAM or OCRAM

Since the memory is not contiguous binary file cannot be used.  More on this latter in FreeRTOS code.
