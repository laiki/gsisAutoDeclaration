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
import gsisDeclaration
import argparse

#%% constands


#%%





#%%

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
          prog='bulkDeclare'
        , description="reads data from csv and creates signed declarations through greeek government portal"
        )
    parser.add_argument('-u', '--user',     dest='user',        default = None, type=str, required=True)
    parser.add_argument('-p', '--password', dest='password',    default = None, type=str, required=True)
    parser.add_argument('--taxid',          dest='taxid',       default = None, type=str, required=True)
    parser.add_argument('--email',          dest='email',       default = None, type=str, required=True)
    parser.add_argument('--receiver',       dest='receiver',    default = None, type=str, required=True)
    parser.add_argument('--download-dir',   dest='download_dir',default = gsisDeclaration.GSIS_DEFAULTS['download_dir'],        type=str, required=False)
    parser.add_argument('--url',            dest='url',         default = gsisDeclaration.GSIS_DEFAULTS['url'],                 type=str, required=False)
    parser.add_argument('--retries',        dest='retries',     default = gsisDeclaration.GSIS_DEFAULTS['retries'],             type=int, required=False)
    parser.add_argument('--web_timeout',    dest='web_timeout', default = gsisDeclaration.GSIS_DEFAULTS['timeout'],             type=int, required=False)
    parser.add_argument('--tesseract_cmd',  dest='tesseract',   default = SMSnotificationParser.SMS_DEFAULTS['tesseract_cmd'],  type=str, required=False)
    parser.add_argument('--sms-timeout',    dest='sms_timeout', default = SMSnotificationParser.SMS_DEFAULTS['timeout'],        type=int, required=False)
    parser.add_argument('--sms-pattern',    dest='sms_pattern', default = SMSnotificationParser.SMS_DEFAULTS['text_pattern'],   type=str, required=False)
    
    args = vars(parser.parse_args())
    sms_receiver = SMSnotificationParser.SMSNotification(text_pattern=args['sms_pattern'], tesseract_cmd=args['tesseract'], timeout=args['sms_timeout'])
    
    # will be used as function ppointer in later processing
    def getSMS():
        return sms_receiver.code
    
    try:
        with gsisDeclaration.gsisGrabber(
                 username   = args['user']
                , password   = args['password']
                , taxid      = args['taxid']
                , email      = args['email']
                , receiver   = args['receiver']
                , text       = '''
this is a test
over multiple
lines
'''
                , download_dir = args['download_dir']
                , url        = args['url']
                , retries    = args['retries']
                , timeout    = args['web_timeout']
                , getCode    = getSMS
                , filename   = "test.pdf"
                ) as gsis:
            url, declaration = gsis.run()
            print(url, declaration)
            
    except Exception as e:
        print(e)

