from collections import deque
import uio
import vtterminal
from micropython import const
import time
import uos
from picocalc_system import screenshot_bmp

sc_char_width =  const(53)
sc_char_height =  const(40)

def ensure_nested_dir(path):
    parts = path.split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current = current + "/" + part if current else part
        try:
            uos.stat(current)
        except OSError:
            uos.mkdir(current)



class vt(uio.IOBase):
    

    def __init__(self,framebuf,keyboard,screencaptureKey=0x15,sd=None,captureFolder="/"): #ctrl+U for screen capture
        if sd != None:
            if not captureFolder.startswith("/"):
                captureFolder = "/"+captureFolder
            captureFolder = '/sd'+captureFolder
            if not captureFolder.endswith("/"):
                captureFolder = captureFolder+"/"
            self.captureFolder = captureFolder
            ensure_nested_dir(self.captureFolder)
            
        self.framebuf = framebuf
        self.sd = sd
        self.keyboardInput = bytearray(30)
        self.outputBuffer = deque((), 30)
        vtterminal.init(self.framebuf)
        self.keyboard = keyboard
        self.screencaptureKey = screencaptureKey
    
    def screencapture(self):
        if self.sd:
            filename = "{}screen_{}.bmp".format(self.captureFolder, time.ticks_ms())
            #with open(filename, "wb") as f:
            #    f.write(self.framebuf.buffer)
            screenshot_bmp(self.framebuf.buffer, filename)
            return True
        return False

    def dryBuffer(self):
        self.outputBuffer = deque((), 30)

        
    def stopRefresh(self):
        self.framebuf.stopRefresh()

    def recoverRefresh(self):
        self.framebuf.recoverRefresh()

    def _care_tick(self):
        try:
            import care

            care.tick()
        except ImportError:
            pass

    def _care_input(self):
        try:
            import care

            care.note_input()
        except ImportError:
            pass

    def wr(self,input):
        #print("WR:", repr(input))
        for c in input:
            if ord(c) == 0x07:
                pass
            else:
                vtterminal.printChar(ord(c))
        return len(input)
    
    def write(self, buf):    
        return self.wr(buf.decode())
    
    def get_screen_size(self):
        return[sc_char_height,sc_char_width]
    
    def _updateInternalBuffer(self):
        s = vtterminal.read()
        if s:
            try:
                self.outputBuffer.extend(ord(ch) for ch in s)
            except TypeError:
                raise ValueError("vtterminal.read() must return str")
            except ValueError:
                raise ValueError("Non-ASCII character in vtterminal.read()")

        n = self.keyboard.readinto(self.keyboardInput)
        if n:
            keys = bytes(self.keyboardInput[:n])
            if self.screencaptureKey in keys:
                self.screencapture()
            self.outputBuffer.extend(self.keyboardInput[:n])
            self._care_input()

    def rd(self):
        while not self.outputBuffer:
            self._updateInternalBuffer()
            if not self.outputBuffer:
                self._care_tick()
                time.sleep_ms(20)

        return chr(self.outputBuffer.popleft())

    def rd_raw(self):
        return self.rd()

    def readinto(self, buf):
        self._updateInternalBuffer()
        count = 0
        buf_len = len(buf)
        for i in range(buf_len):
            if self.outputBuffer:
                buf[i] = self.outputBuffer.popleft()
                count += 1
            else:
                break
        if count:
            self._care_input()
        else:
            self._care_tick()
        return count if count > 0 else None
