# Tiny timer firmware for ATtiny13A.  Usage:  make [all|size|clean]
#
# Toolchain: avr-gcc from PATH, else the one bundled with Arduino IDE.
ARDUINO_AVR := $(HOME)/Library/Arduino15/packages/arduino/tools/avr-gcc/7.3.0-atmel3.6.1-arduino7/bin
AVR_BIN ?= $(if $(shell command -v avr-gcc 2>/dev/null),,$(wildcard $(ARDUINO_AVR))/)
CC      := $(AVR_BIN)avr-gcc
OBJCOPY := $(AVR_BIN)avr-objcopy
SIZE    := $(AVR_BIN)avr-size

MCU    ?= attiny13a
MCU_B  ?= attiny85
F_CPU  ?= 9600000UL
CFLAGS  = -mmcu=$(MCU) -DF_CPU=$(F_CPU) -Os -std=gnu99 -Wall -Wextra \
          $(foreach n,2 3 4 5 6 7 8 9 10,-ffixed-r$(n)) \
          -fno-split-wide-types -fno-tree-ter -fno-move-loop-invariants \
          -ffunction-sections -fdata-sections -fno-jump-tables -flto $(EXTRA)
LDFLAGS = -mmcu=$(MCU) -Wl,--gc-sections -flto -Os

# avrdude: from PATH, else the one bundled with Arduino IDE (macOS location)
ARDUINO_AVRDUDE_DIR := $(wildcard $(HOME)/Library/Arduino15/packages/arduino/tools/avrdude/*)
AVRDUDE ?= $(if $(shell command -v avrdude 2>/dev/null),avrdude,$(firstword $(ARDUINO_AVRDUDE_DIR))/bin/avrdude -C $(firstword $(ARDUINO_AVRDUDE_DIR))/etc/avrdude.conf)
PORT    ?= /dev/cu.usbmodem1101
AVRPART ?= t13
ISP      = $(AVRDUDE) -c stk500v1 -b 19200 -p $(AVRPART) -P $(PORT)

# Optional overrides:  make OSCCAL_VAL=0x5A TONE_HZ=2500 BEEP_MS=800 OLED_FLIP=0
EXTRA  = $(foreach v,OSCCAL_VAL TONE_HZ BEEP_MS AUTO_SLEEP_S OLED_ADDR OLED_FLIP OLED_COM_CFG CAL_MIN FEATURE_BAR FEATURE_BELL,$(if $($(v)),-D$(v)=$($(v))))

OUT   = build
# Library code shared by every program
LIB   = src/oled.c src/render.c
PROGS = timer test_tone test_display test_buttons calib

all: $(PROGS:%=$(OUT)/%.hex) size

$(OUT):
	mkdir -p $(OUT)

# program -> its own source file(s)
SRC_timer        = src/main.c $(LIB)
SRC_test_tone    = src/test_tone.c
SRC_test_display = src/test_display.c $(LIB)
SRC_test_buttons = src/test_buttons.c $(LIB)
SRC_calib        = src/calib.c $(LIB)

.SECONDEXPANSION:
$(OUT)/%.elf: $$(SRC_$$*) $(wildcard src/*.h) Makefile | $(OUT)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(SRC_$*)

$(OUT)/%.hex: $(OUT)/%.elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@

# tone_heat: continuous tone for ~20 s (heat test):  make heat FREQ=2000
FREQ ?= 2000
heat: | $(OUT)
	$(CC) $(CFLAGS) $(LDFLAGS) -DHEAT_TEST -DFREQ_HZ=$(FREQ) -o $(OUT)/test_heat.elf src/test_tone.c
	$(OBJCOPY) -O ihex -R .eeprom $(OUT)/test_heat.elf $(OUT)/test_heat.hex
	$(SIZE) -C --mcu=$(MCU) $(OUT)/test_heat.elf

# avr-size report: flash = text+data, RAM (static) = data+bss
size: $(PROGS:%=$(OUT)/%.elf)
	@for p in $(PROGS); do echo "== $$p"; $(SIZE) -C --mcu=$(MCU) $(OUT)/$$p.elf; done

# ---- programming through ArduinoISP (see docs/programowanie.md) -----------
# make sig PORT=/dev/cu.usbmodemXXXX            read the device signature
# make fuses PORT=...                           9.6 MHz, CKDIV8 off, BOD off
# make flash PROG=timer PORT=...                write build/<PROG>.hex
PROG ?= timer
sig:
	$(ISP) -v 2>&1 | grep -E "Device signature|avrdude: .*(error|not in sync|initialization)" || $(ISP) -v

fuses:
	$(ISP) -U lfuse:w:0x7A:m
	$(ISP) -U lfuse:r:-:h -U hfuse:r:-:h

flash: build/$(PROG).hex
	$(ISP) -U flash:w:build/$(PROG).hex:i

# Plan B: ATtiny25/45/85 (8 MHz internal oscillator, same pins) with the
# optional frame (progress bar) and bell icon:  make planb MCU=attiny85
planb:
	$(MAKE) MCU=$(or $(MCU_B),attiny85) F_CPU=8000000UL FEATURE_BAR=1 FEATURE_BELL=1 OUT=build-$(or $(MCU_B),attiny85) all

clean:
	rm -rf build build-attiny25 build-attiny45 build-attiny85

.PHONY: all size clean heat planb sig fuses flash
