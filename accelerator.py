#!/usr/bin/python

import ConfigParser
import os
from datetime import datetime
import subprocess
import logging
import prowlpy

'''
   Copyright 2014 Joshua Bell

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

Config=ConfigParser.ConfigParser()
Config.read(os.environ['HOME'] + '/bin/acceleratorrc')

logging.basicConfig(filemode='a',
                    filename=Config.get('logging', 'transmissionOutput'),
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

logging.info("Starting Accelerator Run at " + str(datetime.now()))
# logging.info("Here's the Environment:")
# logging.info(str(os.environ))

# Translate Torrent Env Vars
try: 
torrentDir = os.environ['TR_TORRENT_DIR'] 
torrentName = os.environ['TR_TORRENT_NAME']
torrentPath = os.path.join(torrentDir, torrentName)

def pushNotification(application="Accelerator Transcoding", title="Encoding Status", message="Transcode Completed"):
 
    p = prowlpy.Prowl(Config.get('pushsettings', 'prowlApiKey'))
    
    try:
        p.add(application, title, message, 1, None, None)
        logging.info('Successfully sent Push Notification')
    except Exception,msg:
        logging.error(msg)  

def encodeFile(inputDir=torrentDir + '/', inputFile=torrentName, outputDir=Config.get('output','outputDir') + '/', outputFile=None):

    if outputFile is None:
        logging.info("Determining file extension")
        if os.path.splitext(inputFile)[1] != ".mkv":
            logging.warn("We don't handle anything but mkv formatted files")
            logging.warn("Input file name is: " + inputFile)
            sys.exit('Exiting: input file was not mkv, it was ' + inputFile)
        logging.info("Determining Output file name")
        outputFile = os.path.splitext(inputFile)[0] + ".mp4"
        logging.info("Output file name is: " + outputFile)

    logging.info("Transcoding file: " + inputDir + inputFile) 
    logging.info("Outputing to: " + outputDir + outputFile) 
    # Encode the File
    # Figure out how to log output below
    encoderLog = open(Config.get('logging', 'conversionLog'), 'a')

    encode = subprocess.check_call([Config.get('encoder', 'app'), "-i", inputDir + inputFile, "-o",  outputDir + outputFile, "-Z", Config.get('encoder', 'preset')],stdout=encoderLog, stderr=subprocess.STDOUT)
    logging.info("Return Code of encode process: " + str(encode))
    logging.info("Finished Encoding")

    return outputFile


if os.path.isdir(torrentPath):
    logging.info("Directory Torrent Detected")
    for videoFile in os.listdir(torrentPath):
        logging.info("Encoding " + videoFile + " from directory " + torrentPath) 
        transcodedFile = encodeFile(inputDir=torrentPath + "/", inputFile=videoFile)
        logging.info("Finished Encoding - log outside of encode function")
        logging.info("Opening Output in iDentify " + transcodedFile)
        tagging = subprocess.call(["/usr/bin/open", "-a","/Applications/iDentify.app",Config.get('output','outputDir') + '/' + transcodedFile])
        pushNotification(message='Transcode of ' + videoFile + ' is complete.')

    pushNotification(message='Transcode of ' + torrentName + ' is complete.')
else:
    logging.info("Encoding a Single File") 
    transcodedFile = encodeFile()
    logging.info("Finished Encoding - log outside of encode function")
    logging.info("Opening Output in iDentify " + transcodedFile)
    tagging = subprocess.call(["/usr/bin/open", "-a","/Applications/iDentify.app",Config.get('output','outputDir') + '/' + transcodedFile])
    pushNotification(message='Transcode of ' + torrentName + ' is complete.')

logging.info("End Processing of " + torrentPath + " at: " + str(datetime.now()))
