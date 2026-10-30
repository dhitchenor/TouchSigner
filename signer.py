#!/usr/bin/env python3

# Trying to make it easier to insert handwritten signatures in a digital age.
# Cause I don't have a scanner.
# by moosd 2015
#
# Updated for Python3/svg output, by Dale Hithenor

import sys, os, pygame
import operator
from itertools import islice
from tkinter import filedialog
import tkinter as tk

# OPTIONS TO CHANGE
line_thickness = 6
antialiasing = False
window_fraction = 2 / 3
resize_on_save = False

# REST OF CODE FOLLOWS:

def save_svg(path, pts, size):
    # Pad by half the stroke so the line isn't clipped at the bounding box edges
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

def scaler(p, scalefac):
    # Same multiplier on both axes, otherwise the signature takes on the window's aspect ratio
    side = min(window_size)
    return (int((p[0] - minwidth) / scalefac * side), int((p[1] - minheight) / scalefac * side))

def reinit_vars():
    global points, minwidth, minheight, maxwidth, maxheight
    points = []
    maxwidth = 1
    maxheight = 1
    minwidth = 0
    minheight = 0

pygame.init()

# [0] is the primary monitor; Info().current_w could span all monitors on some multi-head setups
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
            sys.exit()
        elif event.type == pygame.KEYUP:
            kmap = pygame.key.get_pressed()
            if event.key == pygame.K_q:
                sys.exit()
            if event.key == pygame.K_ESCAPE:
                del points
                reinit_vars()
                stage = 0
            if event.key == pygame.K_F4 and (kmap[pygame.K_LALT] or kmap[pygame.K_RALT]):
                sys.exit()
            if event.key == pygame.K_RETURN:
                pygame.event.set_grab(0)
                pygame.mouse.set_visible(1)
                root = tk.Tk()
                root.withdraw()
                f = filedialog.asksaveasfilename(defaultextension=".png")
                root.destroy()
                # Cancel returns "" on current Tk, () on some older builds
                if not f:
                    pygame.mouse.set_visible(0)
                    pygame.event.set_grab(1)
                    continue
                base = os.path.splitext(f)[0]

                if resize_on_save:
                    scalefac = max(maxwidth - minwidth, maxheight - minheight)
                    out_pts = [scaler(p, scalefac) for p in points]
                    out_size = window_size
                else:
                    out_pts = [(x - minwidth, y - minheight) for x, y in points]
                    out_size = (maxwidth - minwidth, maxheight - minheight)

                tosave = pygame.Surface(out_size, pygame.SRCALPHA, 32).convert_alpha()
                for p1, p2 in window(out_pts, 2):
                    if antialiasing:
                        pygame.draw.aaline(tosave, (0,0,0), p1, p2)
                    else:
                        pygame.draw.line(tosave, (0,0,0), p1, p2, line_thickness)
                pygame.image.save(tosave, base + ".png")
                save_svg(base + ".svg", out_pts, out_size)
                print(f"Saved {base}.png and {base}.svg")
                sys.exit()
        elif event.type == pygame.MOUSEMOTION:
            points.append(pygame.mouse.get_rel())
            if len(points) > 1:
                stage = 1
                points[-1] = tuple(map(operator.add, points[-2], points[-1]))
            maxheight = max([x[1] for x in points])
            maxwidth = max([x[0] for x in points])
            minheight = min([x[1] for x in points])
            minwidth = min([x[0] for x in points])
            if maxwidth == 0: maxwidth = 1
            if maxheight == 0: maxheight = 1

    if stage == 0:
        screen.blit(background, (0,0))
    elif stage == 1:
        screen.fill(blank)
        for pos1, pos2 in window(points, 2):
            scalefac = max([maxwidth - minwidth, maxheight - minheight])
            p1 = scaler(pos1, scalefac)
            p2 = scaler(pos2, scalefac)
            if antialiasing:
                pygame.draw.aaline(screen, (0,0,0), p1, p2)
            else:
                pygame.draw.line(screen, (0,0,0), p1, p2, line_thickness)
    pygame.display.flip()
