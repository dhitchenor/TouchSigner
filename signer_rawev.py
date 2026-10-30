#!/usr/bin/env python3

# Trying to make it easier to insert handwritten signatures in a digital age.
# Cause I don't have a scanner.
# by moosd 2015
#
# Updated for Python3/svg output, by Dale Hithenor

# This version reads raw touchpad events rather than using mouse relative movements
# Linux specific!

import sys, pygame, os
import operator
from itertools import islice
from tkinter import filedialog
import tkinter as tk
import struct
import time
import threading

# OPTIONS TO CHANGE
line_thickness = 6
antialiasing = False
window_fraction = 2 / 3
resize_on_save = False
events_location = "/dev/input/by-path/platform-i8042-serio-1-event-mouse"
ww = 4500
hh = 3500

# REST OF CODE FOLLOWS:

def save_svg(path, pts, size):
    # Pad by half the stroke so the line isn't clipped at the edges
    pad = line_thickness / 2
    w, h = size
    coords = " ".join(f"{x},{y}" for x, y in pts)
    with open(path, "w") as fh:
        fh.write(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2*pad}" height="{h + 2*pad}" '
            f'viewBox="{-pad} {-pad} {w + 2*pad} {h + 2*pad}">\n'
            f'  <polyline points="{coords}" fill="none" stroke="black" '
            f'stroke-width="{line_thickness}" stroke-linecap="round" stroke-linejoin="round"/>\n'
            '</svg>\n'
        )

def draw_instructions(instructions):
    font = pygame.font.Font(None, 24)
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))
    n = 0
    for t in instructions:
        text = font.render(t, 1, (10, 10, 10))
        textpos = text.get_rect()
        textpos.centerx = background.get_rect().centerx
        n += 24
        background.blit(text, (textpos.left, n))
    return background

def window(seq, n=2):
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def scaler(p):
    # One factor for both axes so the touchpad's aspect ratio survives any window shape
    s = min(window_size[0] / ww, window_size[1] / hh)
    return (int(p[0] * s), int(p[1] * s))

def reinit_vars():
    global points
    points = []

timeout = 0
touch = 0

def listener():
    global timeout, points, stage
    FORMAT = 'llHHi'
    EVENT_SIZE = struct.calcsize(FORMAT)
    x = y = 0
    moved = False
    with open(events_location, "rb") as in_file:
        while event := in_file.read(EVENT_SIZE):
            (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)
            if type == 3 and code == 1:
                if not timeout > time.time():
                    reinit_vars()
                    stage = 1
                timeout = time.time() + 0.2
            elif type == 3 and code == 53:
                x = value - 1210
                moved = True
            elif type == 3 and code == 54:
                y = value - 1250
                moved = True
            # evdev only reports axes that changed, so commit on SYN_REPORT rather
            # than on Y, or purely horizontal strokes get dropped
            elif type == 0 and code == 0 and moved:
                points.append([x, y])
                moved = False

lthread = threading.Thread(target=listener)
lthread.start()

pygame.init()

# [0] is the primary monitor; Info().current_w would span all monitors on some multi-head setups
desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
window_size = (int(desktop_w * window_fraction), int(desktop_h * window_fraction))

screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("TouchSigner")

pygame.mouse.set_visible(0)
pygame.event.set_grab(1)

instructions = ["Use your touchpad to draw a signature and hit enter when done.", "Esc = reset", "q = quit"]
stage = 0

background = draw_instructions(instructions)
blank = 255, 255, 255

reinit_vars()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            os._exit(0)
        elif event.type == pygame.KEYUP:
            kmap = pygame.key.get_pressed()
            if event.key == pygame.K_q:
                os._exit(0)
            if event.key == pygame.K_ESCAPE:
                del points
                reinit_vars()
                stage = 0
            if event.key == pygame.K_F4 and (kmap[pygame.K_LALT] or kmap[pygame.K_RALT]):
                os._exit(0)
            if event.key == pygame.K_RETURN:
                # Snapshot now: the listener thread would otherwise treat cursor movement
                # in the save dialog as a new touch and replace the signature
                pts = [tuple(p) for p in points]
                pygame.event.set_grab(0)
                pygame.mouse.set_visible(1)
                root = tk.Tk()
                root.withdraw()
                f = filedialog.asksaveasfilename(defaultextension=".png")
                root.destroy()
                # Cancel returns "" on current Tk, () on some older builds
                if not f:
                    points = pts
                    stage = 1
                    pygame.mouse.set_visible(0)
                    pygame.event.set_grab(1)
                    continue
                base = os.path.splitext(f)[0]

                if resize_on_save:
                    out_pts = [scaler(p) for p in pts]
                    out_size = window_size
                else:
                    out_pts = pts
                    out_size = (ww, hh)

                tosave = pygame.Surface(out_size, pygame.SRCALPHA, 32).convert_alpha()
                for p1, p2 in window(out_pts, 2):
                    if antialiasing:
                        pygame.draw.aaline(tosave, (0,0,0), p1, p2)
                    else:
                        pygame.draw.line(tosave, (0,0,0), p1, p2, line_thickness)
                pygame.image.save(tosave, base + ".png")
                save_svg(base + ".svg", out_pts, out_size)
                print(f"Saved {base}.png and {base}.svg")
                os._exit(0)

    if stage == 0:
        screen.blit(background, (0,0))
    elif stage == 1:
        screen.fill(blank)
        for pos1, pos2 in window(points, 2):
            p1 = scaler(pos1)
            p2 = scaler(pos2)
            if antialiasing:
                pygame.draw.aaline(screen, (0,0,0), p1, p2)
            else:
                pygame.draw.line(screen, (0,0,0), p1, p2, line_thickness)
    pygame.display.flip()
