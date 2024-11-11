# Introduction

Cupboard is an educational software tool to emulate the hardware components that support classic 8-bit CPUs such as RAM, ROM, clocks, timers, and other peripherals. A Cupboard user will be able to plug their physical 8-bit CPU into an adapter board. This board then provides power, clock, reset, and control logic as well as the memory bus with emulated RAM, ROM, and other memory-mapped I/O.

___NOTE:___  _Cupboard is spell-corrected version of "cpuboard". It supports your CPUs, not your cups. Sorry for any confusion._

## Features

Cupboard controls the array of electrical signals that drive the physical CPU. Thus, it can emulate any state or condition and inspect the outcome with great flexibility. This includes:
  * memory access with the ability to load and inspect memory
  * emulate timing events and other interrupts
  * emulate memory-mapped I/O such as communication interfaces

It is limited to emulating static or "low-speed" (by modern standards) interactions. Early prototypes show that clock speeds approaching 100 kHz should be possible. But, that is one or two orders of magnitude slower than real hardware. As the project matures, increasing the maximum emulated clock rates will be a goal.

## Supported Devices

The initial design will target the 65C02. However, adapting this to support various CPUs should be easy. Additional devices to consider include the Z80, 8080, 8085, and 6809.

The primary limitation of the supported CPU is that it must have a static memory core. That is, it must be able to preserve internal state when the clock is halted. Early NMOS designs of these chips used dynamic RAM for registers, and these would lose state if the clock stopped. Fortunately, most parts have modern CMOS equivalents that can be single-stepped.

# Design

This project depends on an adapter board that electrically interfaces with the target CPU. Initially, the Adafruit "Metro M4 Grand Central" board is used. It can directly access over 40 gpio lines. This makes it capable of supporting a wide range of devices at a high rate of speed.

___CAUTION:___  _The M4 Grand Central is limited to 3.3-volt logic on most pins. Porting this to boards that support a 5-volt interface should be trivial._

___DISCLAIMER:___  _This design will be incrementally built in haphazard stages that won't make much sense upon retrospection. That's not my goal. This project is, in and of itself, and educational exercise for the author.  ;-)  I'll try to leave plenty of breadcrumbs in hopes that others are fed along the way. --EWS_

## Concept Stages

Here's and overview of how work is expected to unfold.  I'll document each stage more fully below as I get to them.
  1. Make It Work  __<-- We are here__
  1. Make It Better
     1. UI improvements
     1. Additional device support
     1. Additional CPU support
     1. Basic speed-up
  1. Make It Good
     1. Improve integration ability
     1. Improve speed

### Stage 1: Make It Work

In this stage, the goal is to make it work via any quick and hacky methods possible on any hardware available. It's a proof of concept only.

To this end, I have a 65C02 and an Metro M4 Grand Central. This Grand Central board can be readily used in Arduino or in Circuit Python mode by swapping the bootloader. For the initial build, speed isn't an issue, so Python it is.

### Stage 2: Make It Better

In this stage, I'll initially improve the user interface. Later, I'll look into additional CPU and device support. Finally, I'll take the first pass at optimizing performance.

### Stage 3: Make It Good

This final stage will focus on usability and speed.
