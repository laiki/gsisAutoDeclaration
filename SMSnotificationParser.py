# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 17:40:10 2025

@author: wgout

requires 
- a tesseract installation supporting greek, german and english languages
- a german Windows system as the notification control is beein identified by its Name 
"""



import pytesseract
from PIL import ImageGrab
import pyautogui
import uiautomation as auto
import time
import re
from screeninfo import get_monitors
import pandas as pd
import argparse

#%% defaults

SMS_DEFAULTS = {
          'text_pattern'  : "(\d{6})\s+ΚΩΔΙΚΟΣ ΓΙΑ ΕΚΔΟΣΗ"
        , 'tesseract_cmd' : r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        , 'timeout'       : 60 
        , 'notification_center_name' : "Benachrichtigungscenter"
        , 'clear_button_label'      : "Alle löschen"
    
    }
 


#%%

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class SMSNotification( metaclass=Singleton ):
    MESSAGE_PIXEL_WIDHT = 300
    PIXEL_OFFSET_NOTIFIER_X_POSITION = -20
    PIXEL_OFFSET_NOTIFIER_Y_POSITION = -20


    def __init__(  self, text_pattern : str, tesseract_cmd : str, timeout : int
                 , notification_center_name = SMS_DEFAULTS['notification_center_name']
                 , clear_button_label = SMS_DEFAULTS['clear_button_label']):
        self.text_pattern  = re.compile(text_pattern)
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.timeout       = timeout
        self.notification_center_name = notification_center_name
        
        self.clear_button_label = clear_button_label
        
        
        monitors = list()
        for m in get_monitors():
            monitor = {'name' : m.name, 'x' : m.x, 'y' : m.y, 'width' : m.width, 'height' : m.height, 'is_primary' : m.is_primary }
            monitors.append(monitor)
        
        displays = pd.DataFrame(monitors)
        self.primary_display = displays[displays.is_primary].iloc[0]
        self.bbox = ( int(self.primary_display.x + self.primary_display.width - SMSNotification.MESSAGE_PIXEL_WIDHT), int(self.primary_display.y),
                      int(self.primary_display.x + self.primary_display.width), int(self.primary_display.y + self.primary_display.height) )
            
        self.notification_x_click_position = int( self.primary_display.x + self.primary_display.width + SMSNotification.PIXEL_OFFSET_NOTIFIER_X_POSITION )
        self.notification_y_click_position = int( self.primary_display.y + self.primary_display.height + SMSNotification.PIXEL_OFFSET_NOTIFIER_Y_POSITION )
        
        self.click_clear_all_button()
            
    def _click_notification_icon(self):            
        pyautogui.click(self.notification_x_click_position, self.notification_y_click_position)
        time.sleep(1)
        return


    def _extract_code_from_text(self, text):
        match = re.search(self.text_pattern, text)
        if match:
            return match.group(1)
        return None

    def _capture_notification_area(self):
        return ImageGrab.grab(bbox=self.bbox)  



    # Extrahiere den 6-stelligen Code aus dem bekannten Textmuster
    def _extract_code(self, text):        
        match = re.search(self.text_pattern, text)
        if match:
            return match.group(1)
        return None
    

    def click_clear_all_button(self):
        cleared = False
        self._click_notification_icon()
        time.sleep(1)
        root = auto.GetRootControl()
        # Suche nach dem Benachrichtigungscenter-Fenster
        for control in root.GetChildren():
            if self.notification_center_name in control.Name:
                # Suche innerhalb des Fensters nach dem Button
                clear_button = control.Control(searchDepth=10, Name=self.clear_button_label)
                if clear_button.Exists(0, 0):
                    clear_button.Click()
                    cleared = True
        return cleared

    def wait_for_sms_code(self):
        start = time.time()
        while (time.time() - start) < self.timeout:
            self._click_notification_icon()
            screenshot = self._capture_notification_area()
            text = pytesseract.image_to_string(screenshot, lang='ell+deu+eng')
            code = self._extract_code(text)
            if code:
                print("code found:", code)
                self.click_clear_all_button()
                return code
            time.sleep(1)
        print("SMS code receiver timeout.")
        return None
    
    @property
    def code(self):
        return self.wait_for_sms_code()


#%% main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
          prog='SMSNotificationParser'
        , description="tries to retreive SMS codes receieved and shown in the Windows Notification bar"
        )
    parser.add_argument('-p', '--pattern', dest='pattern',   default=SMS_DEFAULTS['text_pattern'])
    parser.add_argument('--tesseract_cmd', dest='tesseract', default=SMS_DEFAULTS['tesseract_cmd'])
    parser.add_argument('-t', '--timeout', dest='timeout',   default=SMS_DEFAULTS['timeout'])
    parser.add_argument('--notification-center-name', dest='notification_center_name',   default=SMS_DEFAULTS['notification_center_name'])
    parser.add_argument('--clear-button-label', dest='clear_button_label',   default=SMS_DEFAULTS['clear_button_label'])
    args = vars(parser.parse_args())
    sms_receiver = SMSNotification(  text_pattern=args['pattern']
                                   , tesseract_cmd=args['tesseract']
                                   , timeout=args['timeout']
                                   , notification_center_name=args['notification_center_name']
                                   , clear_button_label=args['clear_button_label'])
    sms_code = sms_receiver.code
    if not sms_code is None:
        print("sms_code:", sms_code)
    else:
        print("no SMS code received, termination")

        

#%%
