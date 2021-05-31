Interrupt Registers
===================

The interrupt register is used to indicate the status or errors from hardware. These registers have five additional registers that associated with them. These registers are:

- **Interrupt Register (INT)**: The raw status of interrupt. It's not very useful since it only shows the current status of signal without any additional processing.

- **Trigger Register (TRIG)**: The trigger register selects how the error or status signal is trapped. It can be set to level high sensitive (``0``) or positive edge sensitive (``1``).

- **Trap Register (TRAP)**: The active error or status is trapped in this register. The values in the trap register are bitwise cleared by writing bit 1 in the corresponding position.

- **Mask Register (MASK)**: The mask register is the interrupt mask for the trapped error or status. And it controls whether an IRQ signal will be generated. Bit 1 in mask register enables interrupt generation. Note that interrupt source that are masked still will be indicated in the trap register.

- **Software Force Register (FORCE)**: The software force register is only for debug the test purposes to force a bit in the trap register. Writing bit 1 in this register will set the corresponding bit in the trap register.

- **Debug Register (DBG)**: The debug register is a mirror of the trap register.
