# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 12:02:39 2025

@author: wgout
"""


import pytesseract
from PIL import ImageGrab
import pyautogui
import uiautomation as auto
import time
import re
from screeninfo import get_monitors
import pandas as pd
import SMSnotificationParser
import argparse

#%% constands


#%%


class gsisDeclarationCreator(metaclass=Singleton):
    def __init__(self):
        pass
    


#%%

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
          prog='gsisDeclarationCreator'
        , description="reads data from Excel and creates signed declarations through greeek government portal"
        )
    parser.add_argument('-p', '--pattern', dest='pattern',   default=SMSnotificationParser.SMS_DEFAULTS['text_pattern'])
    parser.add_argument('--tesseract_cmd', dest='tesseract', default=SMSnotificationParser.SMS_DEFAULTS['tesseract_cmd'])
    parser.add_argument('-t', '--timeout', dest='timeout',   default=SMSnotificationParser.SMS_DEFAULTS['timeout'])
    args = vars(parser.parse_args())
    sms_receiver = SMSnotificationParser.SMSNotification(text_pattern=args['pattern'], tesseract_cmd=args['tesseract'], timeout=args['timeout'])
    sms_code = sms_receiver.code
    print("sms code:", sms_code)
