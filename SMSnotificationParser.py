# -*- coding: utf-8 -*-
"""
This module provides functionality to parse SMS notifications from the Windows Notification Center.

It is designed to extract a verification code from SMS messages that are displayed as notifications.
This script requires a Tesseract OCR installation with support for Greek, German, and English,
and it is intended to run on a German Windows system where the notification center is identified by
the name "Benachrichtigungscenter".

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
from datetime import datetime as dt
import pathlib
from loguru import logger as lg
import logger

#%% defaults

SMS_DEFAULTS = {
          'text_pattern'  : r".*(\d{6})\s+ΚΩΔΙΚΟΣ ΓΙΑ ΕΚΔΟΣΗ.*|.*GOVGR.+(\d{6})\s+.*"
        , 'tesseract_cmd' : r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        , 'timeout'       : 120 
        , 'notification_center_name': "Benachrichtigungscenter"
        , 'clear_button_label'      : "Alle löschen"
        , 'debug'                   : False
    }
 
#%% constants

DEBUG_DIR = pathlib.Path('./debug')

#%%

class Singleton(type):
    """
    A metaclass for creating singleton classes.

    This metaclass ensures that only one instance of a class is created. If an instance
    already exists, it returns the existing instance instead of creating a new one.

    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class SMSNotification( metaclass=Singleton ):
    """
    A class to handle SMS notifications from the Windows Notification Center.

    This class captures screenshots of the notification area, uses OCR to extract text,
    and parses the text to find a specific code based on a regex pattern. It is implemented
    as a singleton to ensure only one instance manages the notification area.

    """
    MESSAGE_PIXEL_WIDHT = 300
    PIXEL_OFFSET_NOTIFIER_X_POSITION = -20
    PIXEL_OFFSET_NOTIFIER_Y_POSITION = -20


    @logger.logging     
    @lg.catch
    def __init__(  self, text_pattern : str, tesseract_cmd : str, timeout : int
                 , notification_center_name = SMS_DEFAULTS['notification_center_name']
                 , clear_button_label = SMS_DEFAULTS['clear_button_label'], debug=SMS_DEFAULTS['debug']):
        """
        Initializes the SMSNotification instance.

        Args:
            text_pattern (str): The regex pattern to find the code in the SMS text.
            tesseract_cmd (str): The file path to the Tesseract OCR executable.
            timeout (int): The maximum time in seconds to wait for an SMS notification.
            notification_center_name (str, optional): The name of the Windows Notification Center.
                Defaults to "Benachrichtigungscenter".
            clear_button_label (str, optional): The label of the "Clear All" button.
                Defaults to "Alle löschen".

        """
        self.debug          = debug
        if self.debug:
            DEBUG_DIR.mkdir(parents= True, exist_ok=True)
            
        self.text_pattern   = re.compile(text_pattern)
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.timeout        = timeout
        self.notification_center_name   = notification_center_name
        
        self.clear_button_label         = clear_button_label
        
        
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
    
    @logger.logging     
    @lg.catch
    def _click_notification_icon(self):
        """
        Clicks the notification icon to open the Notification Center.

        This method simulates a mouse click at the coordinates of the notification icon
        to ensure the notification area is visible for capturing.

        """
        pyautogui.click(self.notification_x_click_position, self.notification_y_click_position)
        time.sleep(1)
        return


    @logger.logging     
    @lg.catch
    def _capture_notification_area(self):
        """
        Captures a screenshot of the notification area.

        The notification area is defined by the bounding box `self.bbox`, which is calculated
        based on the primary display's resolution.

        Returns:
            PIL.Image.Image: The captured screenshot as a Pillow Image object.

        """
        return ImageGrab.grab(bbox=self.bbox)  



    @logger.logging     
    @lg.catch
    def _extract_code(self, text):
        """
        Extracts the 6-digit code from the given text based on the regex pattern.

        Args:
            text (str): The text from which to extract the code.

        Returns:
            str: The extracted 6-digit code, or None if no match is found.

        """
        
        match = re.search(self.text_pattern, text)
        if match:
            code = match.group(1)
            lg.success(f"pattern matched, code: {code}")
            return code
        return None
    

    @logger.logging     
    @lg.catch
    def click_clear_all_button(self):
        """
        Clicks the "Clear All" button in the Notification Center.

        This method opens the Notification Center and clicks the "Clear All" button to dismiss
        all notifications, ensuring a clean state for detecting new messages.

        Returns:
            bool: True if the button was clicked, False otherwise.

        """
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

    @logger.logging     
    @lg.catch
    def wait_for_sms_code(self):
        """
        Waits for an SMS code to appear in the Notification Center.

        This method repeatedly captures the notification area, uses OCR to extract text,
        and searches for the code until the timeout is reached. Debug screenshots are saved
        for each attempt if class has been instantiated with debugging enabled.
        The ocr text is been preprocessed by erplacing \n with ; as it showed significant performance increase.

        Returns:
            str: The extracted SMS code, or None if the timeout is reached.

        """
        start = time.time()
        while (time.time() - start) < self.timeout:
            self._click_notification_icon()
            screenshot = self._capture_notification_area()
            text = pytesseract.image_to_string(screenshot, lang='ell+deu+eng')
            
            used_text = text
            if isinstance(text, str):
                used_text = text.replace('\n', ';')
            lg.debug(f"parsing ocr text {used_text}")            
            
            code = self._extract_code(used_text)
            if code:
                lg.success(f"code found: {code}")
                if self.debug:
                    pic = DEBUG_DIR / f"{dt.now().strftime('%Y%m%dT%H%M%S')}_code.png"
                    screenshot.save( pic )
                    lg.debug(f"schreenshot stored at {pic}")                    

                self.click_clear_all_button()
                return code
            # no code received :/
            if self.debug:
                pic = DEBUG_DIR / f"{dt.now().strftime('%Y%m%dT%H%M%S')}_no_code.png"
                screenshot.save( pic )
                lg.warning(f"failed to find pattern in {pic}")
            
            time.sleep(1)
        lg.error("SMS code receiver timeout.")
        return None
    
    @logger.logging     
    @lg.catch
    @property
    def code(self):
        """
        A property to get the SMS code by calling `wait_for_sms_code`.

        Returns:
            str: The extracted SMS code, or None if not found.

        """
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
