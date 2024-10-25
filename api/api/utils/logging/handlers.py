import os
import time
import glob
import zipfile
import codecs
from logging.handlers import TimedRotatingFileHandler


class TimedCompressedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Extended version of TimedRotatingFileHandler that compresses logs on rollover.
    Ensures the log file and directory exist before rollover.
    """

    def ensure_log_file_exists(self):
        """
        Ensure that the log file and directory exist.
        """
        # Ensure the log directory exists
        log_directory = os.path.dirname(self.baseFilename)
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        # Ensure the log file exists
        if not os.path.exists(self.baseFilename):
            with open(self.baseFilename, 'w') as f:
                pass

    def doRollover(self):
        """
        Perform a rollover; a date/time stamp is appended to the filename when
        the rollover happens. If there is a backup count, we get a list of
        matching filenames, sort them and remove the one with the oldest suffix.
        """
        # Ensure the log file exists before proceeding with rollover
        self.ensure_log_file_exists()

        self.stream.close()

        # Get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        time_tuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)

        # Remove the existing file if it exists
        if os.path.exists(dfn):
            os.remove(dfn)

        # Rename the log file
        os.rename(self.baseFilename, dfn)

        # Handle backup count, deleting oldest files if needed
        if self.backupCount > 0:
            s = glob.glob(self.baseFilename + ".20*")
            if len(s) > self.backupCount:
                s.sort()
                os.remove(s[0])

        # Reopen the log file for writing
        if self.encoding:
            self.stream = codecs.open(self.baseFilename, 'w', 'utf-8')  # noqa
        else:
            self.stream = open(self.baseFilename, 'w')

        # Set up the next rollover time
        self.rolloverAt = self.rolloverAt + self.interval

        # Compress the old log file into a zip archive if it exists
        if os.path.exists(dfn):
            if os.path.exists(dfn + ".zip"):
                os.remove(dfn + ".zip")

            with zipfile.ZipFile(dfn + ".zip", "w") as file:
                file.write(dfn, os.path.basename(dfn), zipfile.ZIP_DEFLATED)

            # Remove the uncompressed log file after compression
            os.remove(dfn)
        # else:
        #     # Log or print an error message if the file doesn't exist
        #     print(f"Warning: log file {dfn} not found for compression.")
