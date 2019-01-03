#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from font_fredoka_one import FredokaOne as FontMsg
from font_source_sans_pro import SourceSansPro as FontMeta
from inky import InkyPHAT
from PIL import Image, ImageDraw, ImageFont

MQTT_HOST = "203:4bb0:9ff1:2312:e7f3:b8c4:852:a8b1"
MQTT_TOPIC = "phat-pager"

########################
# MQTT client callbacks
########################

def on_connect(client, userdata, flags, rc):
    print("Connected to " + MQTT_HOST + " with result code: " + str(rc))
    client.subscribe(MQTT_TOPIC + "/#")
    print("Subscribed to topic: " + MQTT_TOPIC)

def on_message(client, userdata, msg):
    message = str(msg.payload)
    print("Received message:\n" + message)
    refresh_screen(message)
    print("Refreshed display with new message")

#########################
# PHAT display functions
#########################

def refresh_screen(json_message):
    # Set up display
    inky_display = InkyPHAT(colour)
    inky_display.set_border(inky_display.BLACK)

    # Image processing functions
    def pixel_icon(source):
        ret_image = Image.new("P", source.size)
        w, h = source.size
        for x in range(w):
            for y in range(h):
                p = source.getpixel((x, y))
                if p[3] > 127:
                    ret_image.putpixel((x, y), inky_display.RED)
        return ret_image

    def pixel_mask(source):
        ret_image = Image.new("1", source.size)
        w, h = source.size
        for x in range(w):
            for y in range(h):
                p = source.getpixel((x, y))
                if p[3] > 127:
                    ret_image.putpixel((x, y), 255)
        return ret_image

    # Create a new canvas to draw on
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT), inky_display.BLACK)
    draw = ImageDraw.Draw(img)

    # Load image files for background
    moon = Image.open("moon.png")
    star = Image.open("star.png")
    star_sm = star.resize((star.width/2, star.height/2))

    # Set up icons and masks for background
    moon_i = pixel_icon(moon)
    moon_m = pixel_mask(moon)
    star_i = pixel_icon(star)
    star_m = pixel_mask(star)
    star_sm_i = pixel_icon(star_sm)
    star_sm_m = pixel_mask(star_sm)

    # Draw background icons on canvas
    img.paste(star_i, (18, 24), star_m)
    img.paste(star_sm_i, (72, 56), star_sm_m)
    img.paste(star_sm_i, (96, 8), star_sm_m)
    img.paste(star_sm_i, (inky_display.WIDTH-star_sm_i.width-4, -8), star_sm_m)
    img.paste(moon_i, (inky_display.WIDTH-moon_i.width-8, inky_display.HEIGHT-moon_i.height-16), moon_m)

    # Load fonts for text
    font_msg = ImageFont.truetype(FontMsg, 18)
    font_meta = ImageFont.truetype(FontMeta, 18)
    
    # Parse message text
    msg = json.loads(json_message)
    ln1 = msg["ln1"]
    ln2 = msg["ln2"]
    ln3 = msg["ln3"]
    ln4 = msg["ln4"]

    # Parse timestamp
    ts = datetime.fromtimestamp(msg["ts"])
    day = ts.strftime("%A")
    time = ts.strftime("%d %b %H:%M")

    # Draw text on canvas
    draw.text((0, 0), ln1, inky_display.WHITE, font=font_msg)
    draw.text((0, 20), ln2, inky_display.WHITE, font=font_msg)
    draw.text((0, 40), ln3, inky_display.WHITE, font=font_msg)
    draw.text((0, 60), ln4, inky_display.WHITE, font=font_msg)
    draw.text((0, inky_display.HEIGHT-20), day, inky_display.RED, font=font_meta)
    day_textsize = draw.textsize(day, font=font_meta)
    draw.text((day_textsize[0]+4, inky_display.HEIGHT-20), time, inky_display.WHITE, font=font_meta)

    # Draw canvas on display
    inky_display.set_image(img)
    inky_display.show()

#################
# Main execution
#################

# Command line arguments to set display colour
parser = argparse.ArgumentParser()
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
args = parser.parse_args()
colour = args.colour

# Connect MQTT client to broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, 1883, 60)
client.loop_forever()
