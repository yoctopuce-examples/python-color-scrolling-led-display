#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is a small demo program showing how to use a Yocto-Color-V2 with
# eight 8x8 RGB LED panels to make a 64x8 full-color scrolling LED display.
#
# The program uses a small Yoctopuce bitmap font file to render
# any string using ISO-latin-1 character set

import os, sys, struct, collections, time

from yocto_api import YAPI, YRefParam
from yocto_colorledcluster import YColorLedCluster

DisplayAddr = "usb"
DisplayWidth = 64
DisplayHeight = 8
RefreshRate = 25

class BitmapFont:
    # Constructor: load and parse a yfm font file
    def __init__(self, yfm_filename):
        self.height = 0
        if not os.path.exists(yfm_filename):
            print("Font file not found:", yfm_filename)
            return
        with open(yfm_filename, 'rb') as file:
            yfm = file.read()
        fields = 'sig ver bpp w h baseline first last'
        YFSHeader = collections.namedtuple('YFSHeader', fields)
        header = YFSHeader._make(struct.unpack("<2sBBHBBBB", yfm[:10]))
        if header.sig != b'YF':
            print("Invalid font file, Yoctopuce yfm file format expected")
            return
        firstc = int(header.first)
        nchar = int(header.last) - firstc + 1
        lsize = int(header.w/8)
        bpos = 10 + 2 * nchar
        fpos = struct.unpack("<"+str(nchar)+"H", yfm[10:bpos])
        # build character-indexed column bitmaps
        self.height = int(header.h)
        self.cwidth = [0] * 256
        self.cbitmap = [[]] * 256
        cidx = 0
        curr_bitmap = [[] for i in range(self.height)]
        for col in range(lsize):
            for bit in range(8):
                ofs = bpos + col
                for y in range(self.height-1, -1, -1):
                    if ((yfm[ofs] << bit) & 0x80) != 0:
                        curr_bitmap[y].append(1)
                    else:
                        curr_bitmap[y].append(0)
                    ofs += lsize
                if 8*col + bit == fpos[cidx]:
                    ch = firstc + cidx
                    self.cwidth[ch] = len(curr_bitmap[0])
                    self.cbitmap[ch] = curr_bitmap
                    curr_bitmap = [[] for i in range(self.height)]
                    cidx = cidx + 1
                    if cidx >= len(fpos): return

    # Tell if a font file was properly loaded
    def isValid(self):
        return self.height > 0

    # Compute the pixel height of a given string
    def stringHeight(self, text):
        return self.height

    # Compute the pixel width of a given string
    def stringWidth(self, text):
        res = 0
        for i in range(len(text)):
            res = res + self.cwidth[ord(text[i])]
        return res

    # Draw a string in a given bi-dimensional RGB buffer
    # Buffer is made of vertical arrays of pixels
    # and is expected to be large enough to hold string
    def drawString(self, text, buffer, x, y, color):
        for idx in range(len(text)):
            c = ord(text[idx])
            cw = self.cwidth[c]
            bitmap = self.cbitmap[c]
            for rx in range(cw):
                for ry in range(self.height):
                    if bitmap[ry][rx] != 0:
                        buffer[x][y+ry] = color
                x += 1

# Draw a bi-dimensional RGB array to a colorLedCluster
# with a shift offset, including clipping if needed
def ShowBitmap(ledCluster, buffer, x = 0, y = 0):
    global DisplayWidth, DisplayHeight
    RGB = [0] * (DisplayWidth * DisplayHeight)
    xstart = ystart = 0
    xstop = len(buffer)
    ystop = len(buffer[0])
    if x < 0:
        xstart = -x
        x = 0
    if y < 0:
        ystart = -y
        y = 0
    if x + xstop - xstart >= DisplayWidth:
        xstop = DisplayWidth - x + xstart
    if y + ystop - ystart >= DisplayHeight:
        ystop = DisplayHeight - y + ystart
    ofs = x * DisplayHeight + y
    dy = ystop - ystart
    for rx in range(xstart, xstop):
        RGB[ofs:ofs+dy] = buffer[rx][ystart:ystop]
        ofs += DisplayHeight
    ledCluster.set_rgbColorArray(0, RGB)

def ScrollText(leds, font):
    # Prepare the pixmap buffer to display
    words = [ 'Post ', 'Tenebras ', 'Lux!     ', 'Post ', 'Tenebras ', 'Lux!     ' ]
    xpos = [ 0 ] * 7
    for idx in range(len(words)):
        xpos[idx + 1] = xpos[idx] + font.stringWidth(words[idx])
    strHeight = font.stringHeight(words[0])
    strWidth = xpos[len(xpos)-1]
    buffer = [[0] * strHeight for i in range(strWidth)]
    font.drawString(words[0], buffer, xpos[0], 0, 0x004000)
    font.drawString(words[1], buffer, xpos[1], 0, 0x000040)
    font.drawString(words[2], buffer, xpos[2], 0, 0x404000)
    font.drawString(words[3], buffer, xpos[3], 0, 0x004000)
    font.drawString(words[4], buffer, xpos[4], 0, 0x000040)
    font.drawString(words[5], buffer, xpos[5], 0, 0x404000)

    # Scroll text at 25 frame/sec
    ref = time.perf_counter()
    itv = 1 / RefreshRate
    pos = DisplayWidth
    while pos > -strWidth:
        t1 = time.perf_counter()
        pos = DisplayWidth - int((t1 - ref) * RefreshRate)
        ShowBitmap(leds, buffer, pos)
        while time.perf_counter() - t1 < itv: pass

def FlashText(leds, font):
    # Prepare the pixmap buffer to display
    text = 'Applause'
    strHeight = font.stringHeight(text)
    strWidth = font.stringWidth(text)
    buffer = [[0] * strHeight for i in range(strWidth)]
    font.drawString(text, buffer, 0, 0, 0x400000)

    # Flash text at 1 Hz, centered
    xpos = (DisplayWidth - strWidth) >> 1
    for i in range(3):
        ShowBitmap(leds, buffer, xpos)
        YAPI.Sleep(500)
        ShowBitmap(leds, buffer, DisplayWidth)
        YAPI.Sleep(500)

errmsg = YRefParam()
if YAPI.RegisterHub(DisplayAddr, errmsg) != YAPI.SUCCESS:
    sys.exit("Init error on hub "+ DisplayAddr + " ("+ errmsg.value+")")

leds = YColorLedCluster.FirstColorLedCluster()
if leds is None:
    sys.exit("No ColorLedCluster found on hub " + DisplayAddr)

font = BitmapFont('Small.yfm')
if not font.isValid():
    sys.exit("Cannot load font file")

ScrollText(leds, font)
FlashText(leds, font)