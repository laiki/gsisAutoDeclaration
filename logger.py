# -*- coding: utf-8 -*-
"""
Created on Sun Oct  5 11:22:52 2025

@author: wgout
"""

from functools import wraps
from loguru import logger 
import pathlib
from datetime import datetime as dt 
import sys

#%% constants
LOG_DIR = pathlib.Path('logs')
LOGFORMAT = "{time} | {level} | {message}"

#%% logic

def logging(f):
    @wraps(f)
    def wrap(*args, **kw):
        logger.trace("enter: %r args[%r, %r]" % \
          (f.__name__, args, kw))
            
        result = f(*args, **kw)

        logger.trace("exit: %r" % \
          (f.__name__))
        return result
    return wrap


def initLogging(args : dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    
    logger.remove()
    logger.add(  LOG_DIR / f"{dt.now().strftime('%Y%m%dT%H%M')}.log"
               , format=LOGFORMAT, level=args.get('log_level', 'CRITICAL')
               , enqueue=True, mode='w'
               , rotation="10 MB", compression="zip"
               )
    logger.add(sys.stderr, format=LOGFORMAT, level="ERROR", colorize=True)
    logger.add(sys.stdout, format=LOGFORMAT, level="INFO", colorize=True)
    
