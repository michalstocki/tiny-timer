#!/usr/bin/env python3
"""Mutation tests: the verifier in design.py must notice typical build errors."""
import copy
import sys
import design as d

base = copy.deepcopy(d.ITEMS)
fails = 0


def run(name, mutate, mode, expect_words):
    global fails
    d.ITEMS[:] = copy.deepcopy(base)
    mutate(d.ITEMS)
    diffs = d.verify(mode)
    hit = any(any(w in x for w in expect_words) for x in diffs)
    print("%-52s %s" % (name, "detected" if hit else "NOT DETECTED  %s" % diffs))
    fails += not hit


def find_wire(items, a, b):
    for it in items:
        if it["kind"] == "wire" and it["a"] == a and it["b"] == b:
            return it
    raise KeyError((a, b))


def find_part(items, ref):
    return next(i for i in items if i["kind"] == "part" and i["ref"] == ref)


run("OLED SDA wire moved to the SCL column", lambda it: find_wire(it, "h26", "b14").update(b="b12"), "work", ["ZWARCIE", "rozerwana", "w jednym otworze"])
run("OLED SDA wire one column off (b15)", lambda it: find_wire(it, "h26", "b14").update(b="b15"), "work", ["rozerwana"])
run("transistor C and E swapped", lambda it: find_part(it, "Q1")["pins"].update(C="d21", E="d19"), "work", ["rozerwana", "ZWARCIE", "w jednym otworze"])
run("emitter wire missing", lambda it: it.remove(find_wire(it, "a21", "T-21")), "work", ["rozerwana"])
run("run button upper pair on the plus rail (short)", lambda it: find_wire(it, "a7", "T-7").update(b="T+7"), "work", ["ZWARCIE"])
run("two parts in one hole", lambda it: find_part(it, "R3")["pins"].update({"1": "a20"}), "work", ["w jednym otworze"])
run("LED reversed", lambda it: find_part(it, "D1")["pins"].update(A="a27", K="a26"), "work", ["rozerwana"])
run("battery + to the minus rail", lambda it: find_wire(it, "BAT:+", "T+30").update(b="T-30"), "work", ["ZWARCIE"])
run("electrolytic C3 reversed", lambda it: find_part(it, "C3")["pins"].update({"+": "T-24", "-": "T+24"}), "work", ["ZWARCIE", "rozerwana"])
run("R1 second leg in the ground strip", lambda it: find_part(it, "R1")["pins"].update({"2": "j14"}), "work", ["ZWARCIE", "rozerwana"])
run("R6 second leg in an unused column (b8)", lambda it: find_part(it, "R6")["pins"].update({"2": "b8"}), "work", ["ZWARCIE", "rozerwana"])


def geometry(mutate, words, name, mode="work"):
    global fails
    d.ITEMS[:] = copy.deepcopy(base)
    mutate(d.ITEMS)
    probs = d.check_geometry(mode)
    hit = any(any(w in x for w in words) for x in probs)
    print("%-52s %s" % (name, "detected" if hit else "NOT DETECTED  %s" % probs))
    fails += not hit


geometry(lambda it: find_part(it, "D1")["pins"].update(A="c26", K="c27"), ["zasłania", "zajmują"], "LED on top of the speaker lead holes")
geometry(lambda it: find_part(it, "R3")["pins"].update({"2": "b21"}), ["rozstaw", "zasłania"], "R3 with a 1-column span")
geometry(lambda it: find_part(it, "R4")["pins"].update({"1": "e24"}), ["rozstaw"], "33 Ω resistor too short for 1/2 W")
d.ITEMS[:] = base
sys.exit(1 if fails else 0)
