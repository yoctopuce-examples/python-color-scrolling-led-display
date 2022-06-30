Sample full-color scrolling LED display driver
==============================================

This repository contains a small demo program showing how to use a [Yocto-Color-V2](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-color-v2) with eight daisy-chained [8x8 Neopixel]("https://www.adafruit.com/product/1487) panels to make a 64x8 full color scrolling LED display.

The interesting part of the code can be found in **scrolling-led-display.py**. Using the same font file **Small.yfm** that we use in the [Yocto-MiniDisplay](https://www.yoctopuce.com/EN/products/usb-displays/yocto-minidisplay), this sample Python software includes:<ul>
<li>a function that takes as input a character string and draws it in a RGB bitmap using a specified color</li>
<li>a fonction that shows a selected section of the RGB bitmap to the LED display</li>
</ul>
By sliding progressively the selected section from left to right, we give the impression that the text is moving from right to left on the display:

![Our USB full-color scrolling LED display](https://www.yoctopuce.com/EN/interactive/img/scrolling-text.gif)

For convenience, we have also included in this directory the two python files from Yoctopuce API that are required to drive the [Yocto-Color-V2](https://www.yoctopuce.com/EN/products/usb-actuators/yocto-color-v2), as well as the architecture-specific DLLs.

For more details, read the full blog post on [www.yoctopuce.com](https://www.yoctopuce.com/EN/article/a-usb-full-color-scrolling-led-display).
