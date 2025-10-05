# -*- coding: utf-8 -*-
"""
This script automates the bulk creation of official declarations using a CSV file as input.

It reads data from a CSV file, where each column represents a recipient and each row
contains the text for the declaration. The script then iterates through the data,
automating the process of logging into the Greek government portal, submitting the
declaration, and downloading the resulting PDF.

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
import pathlib
import itertools
from datetime import datetime as dt
import logger
from functools import wraps
from time import time
from loguru import logger as lg

#%% constands

#%% helper

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        lg.debug('runtime %2.4f sec: func:%r args:[%r, %r]' % \
          (te-ts, f.__name__, args, kw))
        return result
    return wrap


#%% logic

@lg.catch
@logger.logging
@timing
def automate(args):
    """
    Automates the bulk creation of declarations based on the provided arguments.

    This function reads a CSV file, initializes the SMS and GSIS automation tools,
    and then iterates through the CSV data to create and download a declaration
    for each entry. It also generates HTML status reports.

    Args:
        args (dict): A dictionary of command-line arguments containing credentials,
                     file paths, and other configuration settings.

    Raises:
        Exception: If the specified CSV file is not found.

    """
    
    process_start = dt.now()
    csv_file = pathlib.Path(args['csv'])
    if not csv_file.exists():
        raise Exception(f"{csv_file.as_posix()} file not found!")
    
    
    header = pd.read_csv(csv_file, sep = args['csv_sep'], header=None).iloc[0]
    receivers = header.to_list()
    if 'folder' in receivers:
        receivers.remove('folder')
        
    df = pd.read_csv(csv_file, sep = args['csv_sep'])
    
    sms_receiver = SMSnotificationParser.SMSNotification(  text_pattern             = args['sms_pattern']
                                                         , tesseract_cmd            = args['tesseract']
                                                         , timeout                  = args['sms_timeout']
                                                         , notification_center_name = args['notification_center_name']
                                                         , clear_button_label       = args['clear_button_label'] 
                                                         , debug                    = args['debug'] 
                                                         )
    
    # will be used as function pointer in processing
    def getSMS():
        lg.debug('calling sms_receiver.wait_for_sms_code()')
        code = sms_receiver.wait_for_sms_code()
        lg.debug('returned from sms_receiver.wait_for_sms_code():', code)
        return code
    
    status_over_all = list()
    
    full_status = pathlib.Path('downloads') / f"bulk_declare_{process_start.strftime('%Y%m%dT%H%M')}.html"
    pd.DataFrame().to_html(full_status)

    
    for idx, row in df.iterrows():   
        download_dir = pathlib.Path('downloads')        
        if 'folder' in row.index.to_list():
            download_dir = download_dir / row.folder
        download_dir.mkdir(exist_ok=True, parents=True)

        processed = list()
        receiver_list = [ e for e in list(enumerate(header)) if e[1] != 'folder' ]
        for rec in receiver_list: 
            receiver_index = rec[0]
            receiver_name  = rec[1]
            url = None
            declaration = None
            
            text = row.iloc[receiver_index]
            
            try:
                sms_receiver.click_clear_all_button()
                with gsisDeclaration.gsisGrabber(
                          username    = args['user']
                        , password   = args['password']
                        , taxid      = args['taxid']
                        , email      = args['email']
                        , receiver   = receiver_name
                        , download_dir = download_dir.as_posix()
                        , url        = args['url']
                        #, retries    = args['retries']
                        , timeout    = args['web_timeout']
                        , getCode    = getSMS
                        , filename   = "declaration.pdf"
                        , text       = text
                        ) as gsis:
                    url, declaration = gsis.run()
                    lg.success(f"{dt.now()}: declaration {idx}/{receiver_index} of {df.shape[0]}/{len(receiver_list)} for {receiver_name} created")

                    
            except Exception as e:
                lg.exception(e)
            finally:
                sms_receiver.click_clear_all_button()

            
            currrent_status = { 'idx'   : idx 
                               , 'receiver' : receiver_name
                               , 'url'  : url
                               , 'file' : declaration }
            processed.append( currrent_status )
        
        status_over_all.append( processed )
        done = pd.DataFrame(processed)
        singel_status = download_dir / f"{idx}_result.html"
        done.to_html(singel_status)
        lg.success( f"{singel_status} updated" )

        all_done = pd.DataFrame(list(itertools.chain.from_iterable(status_over_all)))
        all_done.to_html(full_status)
        lg.success(f"{full_status} updated" )
    return





#%%

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
          prog='bulkDeclare'
        , description="Reads data from csv and creates signed declarations through greek goverment portal. Created documents will be named declaration.pdf. If file exists, it will receive an numeric index e.g. 'declaration (4).pdf'. The used index will be the next available."
        )
    parser.add_argument(  '-u', '--user', dest='user'
                        , default = None, type=str, required=True
                        , help="Taxisnet cedential." 
                        )
    parser.add_argument(  '-p', '--password', dest='password'
                        , default = None, type=str, required=True
                        , help="Taxisnet cedential." 
                        )
    parser.add_argument(  '--taxid', dest='taxid'
                        , default = None, type=str, required=True
                        , help="Your taxid. Will be used to compare the authentificated user data with your input." )
    parser.add_argument(  '--email', dest='email'
                        , default = None, type=str, required=True
                        , help="Your email address." 
                        )
    parser.add_argument(  '--download-dir', dest='download_dir'
                        , default = gsisDeclaration.GSIS_DEFAULTS['download_dir'], type=str, required=False
                        , help="Folder name to store downloaded file." 
                        )
    parser.add_argument(  '--url', dest='url'
                        , default = gsisDeclaration.GSIS_DEFAULTS['url'], type=str, required=False
                        , help="url to the Hellenic portal used to create the declaration." 
                        )
    parser.add_argument(  '--web_timeout', dest='web_timeout'
                        , default = gsisDeclaration.GSIS_DEFAULTS['timeout'], type=int, required=False
                        , help="Timeout in seconds to wait for a web result." 
                        )
    parser.add_argument(  '--tesseract_cmd',  dest='tesseract'
                        ,   default = SMSnotificationParser.SMS_DEFAULTS['tesseract_cmd'], type=str, required=False
                        , help="Full path to the tesseract.exe binary." )
    parser.add_argument(  '--sms-timeout',    dest='sms_timeout'
                        , default = SMSnotificationParser.SMS_DEFAULTS['timeout'], type=int, required=False
                        , help="Timeout in seconds regarding the SMS reception." 
                        )
    parser.add_argument(  '--sms-pattern',    dest='sms_pattern'
                        , default = SMSnotificationParser.SMS_DEFAULTS['text_pattern'], type=str, required=False
                        , help="SMS text to search for as reguar expression to extract the code." 
                        )
    parser.add_argument(  '--csv', dest='csv'
                        , default = None, type=str, required=True
                        , help="csv input file. Its columns names will be used as receiver of the declaration. If a column named 'folder' is found, the declaration will be stored in the <download-dir>/<folder>." 
                        )
    parser.add_argument(  '--csv-sep', dest='csv_sep'
                        , default = ';', type=str, required=False
                        , help="CSV separator used to read the file." 
                        )
    parser.add_argument(  '--notification-center-name', dest='notification_center_name'
                        , default = SMSnotificationParser.SMS_DEFAULTS['notification_center_name'], type=str, required=False
                        , help="Language settings dependent name of the notification object"
                        )
    parser.add_argument(  '--clear-button-label', dest='clear_button_label'
                        ,  default = SMSnotificationParser.SMS_DEFAULTS['clear_button_label'], type=str, required=False
                        , help="Language settings dependent label of the clear all notifications button."
                        )
    parser.add_argument(  '--debug', dest='debug'
                        ,  default = False, type=bool, required=False
                        , help="Togle debug mode. If activated, folder debug will dontain screenshots of notification area."
                        )
    parser.add_argument(  '--log-level', dest='log_level'
                        ,  default = 'SUCCESS', choices=['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'], required=False
                        , help="level of logging to be used."
                        )
    


                 
    
    args = vars(parser.parse_args())
    logger.initLogging(args)
    lg.debug(f"process started with arguments: {args}")
    
    automate(args)
    
    lg.info("processing finished")
    
