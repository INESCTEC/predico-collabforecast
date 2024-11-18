import os
import time
import glob
import zipfile
import codecs

from logging.handlers import TimedRotatingFileHandler


class TimedCompressedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Extended version of TimedRotatingFileHandler that compress logs on
    rollover.
    """
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the
        filename when the rollover happens.  However, you want the file to be
        named for the start of the interval, not the current time. If there
        is a backup count, then we have to get a list of matching filenames,
        sort them and remove the one with the oldest suffix.
        """

        self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if os.path.exists(dfn):
            os.remove(dfn)
        os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            # find the oldest log file and delete it
            s = glob.glob(self.baseFilename + ".20*")
            if len(s) > self.backupCount:
                s.sort()
                os.remove(s[0])
        # print "%s -> %s" % (self.baseFilename, dfn)
        if self.encoding:
            self.stream = codecs.open(self.baseFilename, 'w', self.encoding)  # noqa
        else:
            with open(self.baseFilename, 'w') as f:
                self.stream = f

        self.rolloverAt = self.rolloverAt + self.interval
        if os.path.exists(dfn + ".zip"):
            os.remove(dfn + ".zip")
        file = zipfile.ZipFile(dfn + ".zip", "w")
        file.write(dfn, os.path.basename(dfn), zipfile.ZIP_DEFLATED)
        file.close()
        os.remove(dfn)
