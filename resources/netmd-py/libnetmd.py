import libusb1
from cStringIO import StringIO
from time import sleep
from struct import pack
try:
    from Crypto.Cipher import DES
    from Crypto.Cipher import DES3
except ImportError:
    DES = None
    DES3 = None
import array
import random

def dump(data):
    if isinstance(data, basestring):
        result = ' '.join(['%02x' % (ord(x), ) for x in data])
    else:
        result = repr(data)
    return result

class defaultUploadEvents:
    def progress(self, current):
        print 'Done: %x/%x (%.02f%%)' % (current, self.total,
                                         current/float(self.total) * 100)
    def trackinfo(self, frames, bytes, format):
        self.total = bytes;


KNOWN_USB_ID_SET = frozenset([
    (0x04dd, 0x7202), # Sharp IM-MT899H
    (0x054c, 0x0075), # Sony MZ-N1 
    (0x054c, 0x0080), # Sony LAM-1 
    (0x054c, 0x0081), # Sony MDS-JB980 
    (0x054c, 0x0084), # Sony MZ-N505 
    (0x054c, 0x0085), # Sony MZ-S1 
    (0x054c, 0x0086), # Sony MZ-N707 
    (0x054c, 0x00c6), # Sony MZ-N10 
    (0x054c, 0x00c7), # Sony MZ-N910
    (0x054c, 0x00c8), # Sony MZ-N710/NF810 
    (0x054c, 0x00c9), # Sony MZ-N510/N610 
    (0x054c, 0x00ca), # Sony MZ-NE410/NF520D 
    (0x054c, 0x00eb), # Sony MZ-NE810/NE910
    (0x054c, 0x0101), # Sony LAM-10
    (0x054c, 0x0113), # Aiwa AM-NX1
    (0x054c, 0x014c), # Aiwa AM-NX9
    (0x054c, 0x017e), # Sony MZ-NH1
    (0x054c, 0x0180), # Sony MZ-NH3D
    (0x054c, 0x0182), # Sony MZ-NH900
    (0x054c, 0x0184), # Sony MZ-NH700/NH800
    (0x054c, 0x0186), # Sony MZ-NH600/NH600D
    (0x054c, 0x0188), # Sony MZ-N920
    (0x054c, 0x018a), # Sony LAM-3
    (0x054c, 0x01e9), # Sony MZ-DH10P
    (0x054c, 0x0219), # Sony MZ-RH10
    (0x054c, 0x021b), # Sony MZ-RH710/MZ-RH910
    (0x054c, 0x022c), # Sony CMT-AH10 (stereo set with integrated MD)
    (0x054c, 0x023c), # Sony DS-HMD1 (device without analog music rec/playback)
    (0x054c, 0x0286), # Sony MZ-RH1
])

def iterdevices(usb_context, bus=None, device_address=None):
    """
      Iterator for plugged-in NetMD devices.

      Parameters:
        usb_context (usb1.LibUSBContext)
          Some usb1.LibUSBContext instance.
        bus (None, int)
          Only scan this bus.
        device_address (None, int)
          Only scan devices at this address on each scanned bus.

      Returns (yields) NetMD instances.
    """
    for device in usb_context.getDeviceList():
        if bus is not None and bus != device.getBusNumber():
            continue
        if device_address is not None and \
           device_address != device.getDeviceAddress():
            continue
        if (device.getVendorID(), device.getProductID()) in KNOWN_USB_ID_SET:
            yield NetMD(device.open())

# XXX: Endpoints numbers are hardcoded
BULK_WRITE_ENDPOINT = 0x02
BULK_READ_ENDPOINT = 0x81

# NetMD Protocol return status (first byte of request)
STATUS_CONTROL = 0x00
STATUS_STATUS = 0x01
STATUS_SPECIFIC_INQUIRY = 0x02
STATUS_NOTIFY = 0x03
STATUS_GENERAL_INQUIRY = 0x04
# ... (first byte of response)
STATUS_NOT_IMPLEMENTED = 0x08
STATUS_ACCEPTED = 0x09
STATUS_REJECTED = 0x0a
STATUS_IN_TRANSITION = 0x0b
STATUS_IMPLEMENTED = 0x0c
STATUS_CHANGED = 0x0d
STATUS_INTERIM = 0x0f

class NetMDException(Exception):
    """
      Base exception for all NetMD exceptions.
    """
    pass

class NetMDNotImplemented(NetMDException):
    """
      NetMD protocol "operation not implemented" exception.
    """
    pass

class NetMDRejected(NetMDException):
    """
      NetMD protocol "operation rejected" exception.
    """
    pass

class NetMD(object):
    """
      Low-level interface for a NetMD device.
    """
    def __init__(self, usb_handle, interface=0):
        """
          usb_handle (usb1.USBDeviceHandle)
            USB device corresponding to a NetMD player.
          interface (int)
            USB interface implementing NetMD protocol on the USB device.
        """
        self.usb_handle = usb_handle
        self.interface = interface
        usb_handle.setConfiguration(1)
        usb_handle.claimInterface(interface)
        if self._getReplyLength() != 0:
            self.readReply()


    def __del__(self):
        try:
            self.usb_handle.resetDevice()
            self.usb_handle.releaseInterface(self.interface)
        except: # Should specify an usb exception
            pass

    def _getReplyLength(self):
        reply = self.usb_handle.controlRead(libusb1.LIBUSB_TYPE_VENDOR | \
                                            libusb1.LIBUSB_RECIPIENT_INTERFACE,
                                            0x01, 0, 0, 4)
        return ord(reply[2])

    def sendCommand(self, command):
        """
          Send a raw binary command to device.
          command (str)
            Binary command to send.
        """
        #print '%04i> %s' % (len(command), dump(command))
        self.usb_handle.controlWrite(libusb1.LIBUSB_TYPE_VENDOR | \
                                     libusb1.LIBUSB_RECIPIENT_INTERFACE,
                                     0x80, 0, 0, command)

    def readReply(self):
        """
          Get a raw binary reply from device.
          Returns the reply.
        """
        reply_length = 0
        while reply_length == 0:
            reply_length = self._getReplyLength()
            if reply_length == 0: sleep(0.1)
        reply = self.usb_handle.controlRead(libusb1.LIBUSB_TYPE_VENDOR | \
                                            libusb1.LIBUSB_RECIPIENT_INTERFACE,
                                            0x81, 0, 0, reply_length)
        #print '%04i< %s' % (len(reply), dump(reply))
        return reply

    def readBulk(self, length):
        """
          Read bulk data from device.
          length (int)
            Length of data to read.
          Returns data read.
        """
        result = StringIO()
        self.readBulkToFile(length, result)
        return result.getvalue()

    def readBulkToFile(self, length, outfile, chunk_size=0x10000, callback=lambda(a):None):
        """
          Read bulk data from device, and write it to a file.
          length (int)
            Length of data to read.
          outfile (str)
            Path to output file.
          chunk_size (int)
            Keep this much data in memory before flushing it to file.
        """
        done = 0
        while done < length:
            received = self.usb_handle.bulkRead(BULK_READ_ENDPOINT,
                min((length - done), chunk_size))
            done += len(received)
            outfile.write(received)
            callback(done)

    def writeBulk(self, data):
        """
          Write data to device.
          data (str)
            Data to write.
        """
        self.usb_handle.bulkWrite(BULK_WRITE_ENDPOINT, data)

ACTION_PLAY = 0x75
ACTION_PAUSE = 0x7d
ACTION_FASTFORWARD = 0x39
ACTION_REWIND = 0x49

TRACK_PREVIOUS = 0x0002
TRACK_NEXT = 0x8001
TRACK_RESTART = 0x0001

ENCODING_SP = 0x90
ENCODING_LP2 = 0x92
ENCODING_LP4 = 0x93

CHANNELS_MONO = 0x01
CHANNELS_STEREO = 0x00

CHANNEL_COUNT_DICT = {
  CHANNELS_MONO: 1,
  CHANNELS_STEREO: 2
}

OPERATING_STATUS_USB_RECORDING = 0x56ff
OPERATING_STATUS_RECORDING = 0xc275
OPERATING_STATUS_RECORDING_PAUSED = 0xc27d
OPERATING_STATUS_FAST_FORWARDING = 0xc33f
OPERATING_STATUS_REWINDING = 0xc34f
OPERATING_STATUS_PLAYING = 0xc375
OPERATING_STATUS_PAUSED = 0xc37d
OPERATING_STATUS_STOPPED = 0xc5ff

TRACK_FLAG_PROTECTED = 0x03

DISC_FLAG_WRITABLE = 0x10
DISC_FLAG_WRITE_PROTECTED = 0x40

DISKFORMAT_LP4 = 0
DISKFORMAT_LP2 = 2
DISKFORMAT_SP_MONO = 4
DISKFORMAT_SP_STEREO = 6

WIREFORMAT_PCM = 0
WIREFORMAT_105KBPS = 0x90
WIREFORMAT_LP2 = 0x94
WIREFORMAT_LP4 = 0xA8

_FORMAT_TYPE_LEN_DICT = {
    'b': 1, # byte
    'w': 2, # word
    'd': 4, # doubleword
    'q': 8, # quadword
}

def BCD2int(bcd):
    """
      Convert BCD number of an arbitrary length to an int.
      bcd (int)
        bcd number
      Returns the same number as an int.
    """
    value = 0
    nibble = 0
    while bcd:
        nibble_value = bcd & 0xf
        bcd >>= 4
        value += nibble_value * (10 ** nibble)
        nibble += 1
    return value

def int2BCD(value, length=1):
    """
      Convert an int into a BCD number.
      value (int)
        Integer value.
      length (int)
        Length limit for output number, in bytes.
      Returns the same value in BCD.
    """
    if value > 10 ** (length * 2 - 1):
        raise ValueError('Value %r cannot fit in %i bytes in BCD' %
             (value, length))
    bcd = 0
    nibble = 0
    while value:
        value, nibble_value = divmod(value, 10)
        bcd |= nibble_value << (4 * nibble)
        nibble += 1
    return bcd

class NetMDInterface(object):
    """
      High-level interface for a NetMD device.
      Notes:
        Track numbering starts at 0.
        First song position is 0:0:0'1 (0 hours, 0 minutes, 0 second, 1 sample)
        wchar titles are probably shift-jis encoded (hint only, nothing relies
          on this in this file)
    """
    def __init__(self, net_md):
        """
          net_md (NetMD)
            Interface to the NetMD device to use.
        """
        self.net_md = net_md

    def send_query(self, query, test=False):
        # XXX: to be removed (replaced by 2 separate calls)
        self.sendCommand(query, test=test)
        return self.readReply()

    def sendCommand(self, query, test=False):
        if test:
            query = [STATUS_SPECIFIC_INQUIRY, ] + query
        else:
            query = [STATUS_CONTROL, ] + query
        binquery = ''.join(chr(x) for x in query)
        self.net_md.sendCommand(binquery)

    def readReply(self):
        result = self.net_md.readReply()
        status = ord(result[0])
        if status == STATUS_NOT_IMPLEMENTED:
            raise NetMDNotImplemented('Not implemented')
        elif status == STATUS_REJECTED:
            raise NetMDRejected('Rejected')
        elif status not in (STATUS_ACCEPTED, STATUS_IMPLEMENTED,
                            STATUS_INTERIM):
            raise NotImplementedError('Unknown returned status: %02X' %
                (status, ))
        return result[1:]

    def formatQuery(self, format, *args):
        result = []
        append = result.append
        extend = result.extend
        half = None
        def hexAppend(value):
            append(int(value, 16))
        escaped = False
        arg_stack = list(args)
        for char in format:
            if escaped:
                escaped = False
                value = arg_stack.pop(0)
                if char in _FORMAT_TYPE_LEN_DICT:
                    for byte in xrange(_FORMAT_TYPE_LEN_DICT[char] - 1, -1, -1):
                        append((value >> (byte * 8)) & 0xff)
                # String ('s' is 0-terminated, 'x' is not)
                elif char in ('s', 'x'):
                    length = len(value)
                    if char == 's':
                        length += 1
                    append((length >> 8) & 0xff)
                    append(length & 0xff)
                    extend(ord(x) for x in value)
                    if char == 's':
                        append(0)
                elif char == '*':
                    extend(ord(x) for x in value)
                else:
                    raise ValueError('Unrecognised format char: %r' % (char, ))
                continue
            if char == '%':
                assert half is None
                escaped = True
                continue
            if char == ' ':
                continue
            if half is None:
                half = char
            else:
                hexAppend(half + char)
                half = None
        assert len(arg_stack) == 0
        return result

    def scanQuery(self, query, format):
        result = []
        append = result.append
        half = None
        escaped = False
        input_stack = list(query)
        def pop():
            return ord(input_stack.pop(0))
        for char in format:
            if escaped:
                escaped = False
                if char == '?':
                    pop()
                    continue
                if char in _FORMAT_TYPE_LEN_DICT:
                    value = 0
                    for byte in xrange(_FORMAT_TYPE_LEN_DICT[char] - 1, -1, -1):
                        value |= (pop() << (byte * 8))
                    append(value)
                # String ('s' is 0-terminated, 'x' is not)
                elif char in ('s', 'x'):
                    length = pop() << 8 | pop()
                    value = ''.join(input_stack[:length])
                    input_stack = input_stack[length:]
                    if char == 's':
                        append(value[:-1])
                    else:
                        append(value)
                # Fetch the remainder of the query in one value
                elif char == '*':
                    value = ''.join(input_stack)
                    input_stack = []
                    append(value)
                else:
                    raise ValueError('Unrecognised format char: %r' % (char, ))
                continue
            if char == '%':
                assert half is None
                escaped = True
                continue
            if char == ' ':
                continue
            if half is None:
                half = char
            else:
                input_value = pop()
                format_value = int(half + char, 16)
                if format_value != input_value:
                    raise ValueError('Format and input mismatch at %i: '
                        'expected %02x, got %02x' % (
                            len(query) - len(input_stack) - 1,
                            format_value, input_value))
                half = None
        assert len(input_stack) == 0
        return result

    def acquire(self):
        """
          Exclusive access to device.
          XXX: what does it mean ?
        """
        query = self.formatQuery('ff 010c ffff ffff ffff ffff ffff ffff')
        reply = self.send_query(query)
        self.scanQuery(reply, 'ff 010c ffff ffff ffff ffff ffff ffff')

    def release(self):
        """
          Release device previously acquired for exclusive access.
          XXX: what does it mean ?
        """
        query = self.formatQuery('ff 0100 ffff ffff ffff ffff ffff ffff')
        reply = self.send_query(query)
        self.scanQuery(reply, 'ff 0100 ffff ffff ffff ffff ffff ffff')

    def getStatus(self):
        """
          Get device status.
          Returns device response (content meaning is largely unknown).
        """
        query = self.formatQuery('1809 8001 0230 8800 0030 8804 00 ff00 ' \
                                 '00000000')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1809 8001 0230 8800 0030 8804 00 ' \
                              '1000 000900000 %x')[0]

    def isDiskPresent(self):
        """
          Is a disk present in device ?
          Returns a boolean:
            True: disk present
            False: no disk
        """
        status = self.getStatus()
        return status[4] == 0x40

    def getOperatingStatus(self):
        query = self.formatQuery('1809 8001 0330 8802 0030 8805 0030 8806 ' \
                                 '00 ff00 00000000')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1809 8001 0330 8802 0030 8805 0030 ' \
                              '8806 00 1000 00%?0000 0006 8806 0002 %w')[0]

    def _getPlaybackStatus(self, p1, p2):
        query = self.formatQuery('1809 8001 0330 %w 0030 8805 0030 %w 00 ' \
                                 'ff00 00000000',
                                 p1, p2)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1809 8001 0330 %?%? %?%? %?%? %?%? ' \
                              '%?%? %? 1000 00%?0000 %x')[0]

    def getPlaybackStatus1(self):
        return self._getPlaybackStatus(0x8801, 0x8807)

    def getPlaybackStatus2(self):
        # XXX: duplicate of getOperatingStatus
        return self._getPlaybackStatus(0x8802, 0x8806)

    def getPosition(self):
        query = self.formatQuery('1809 8001 0430 8802 0030 8805 0030 0003 ' \
                                 '0030 0002 00 ff00 00000000')
        try:
            reply = self.send_query(query)
        except NetMDRejected: # No disc
            result = None
        else:
            result = self.scanQuery(reply, '1809 8001 0430 %?%? %?%? %?%? ' \
                                    '%?%? %?%? %?%? %?%? %? %?00 00%?0000 ' \
                                    '000b 0002 0007 00 %w %b %b %b %b')
            result[1] = BCD2int(result[1])
            result[2] = BCD2int(result[2])
            result[3] = BCD2int(result[3])
            result[4] = BCD2int(result[4])
        return result

    def _play(self, action):
        query = self.formatQuery('18c3 ff %b 000000', action)
        reply = self.send_query(query)
        self.scanQuery(reply, '18c3 00 %b 000000')

    def play(self):
        """
          Start playback on device.
        """
        self._play(ACTION_PLAY)

    def fast_forward(self):
        """
          Fast-forward device.
        """
        self._play(ACTION_FASTFORWARD)

    def rewind(self):
        """
          Rewind device.
        """
        self._play(ACTION_REWIND)

    def pause(self):
        """
          Pause device.
        """
        self._play(ACTION_PAUSE)

    def stop(self):
        """
          Stop playback on device.
        """
        query = self.formatQuery('18c5 ff 00000000')
        reply = self.send_query(query)
        self.scanQuery(reply, '18c5 00 00000000')

    def gotoTrack(self, track):
        """
          Seek to begining of given track number on device.
        """
        query = self.formatQuery('1850 ff010000 0000 %w', track)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1850 00010000 0000 %w')[0]

    def gotoTime(self, track, hour=0, minute=0, second=0, frame=0):
        """
          Seek to given time of given track.
        """
        query = self.formatQuery('1850 ff000000 0000 %w %b%b%b%b', track,
                                 int2BCD(hour), int2BCD(minute),
                                 int2BCD(second), int2BCD(frame))
        reply = self.send_query(query)
        return self.scanQuery(reply, '1850 00000000 %?%? %w %b%b%b%b')

    def _trackChange(self, direction):
        query = self.formatQuery('1850 ff10 00000000 %w', direction)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1850 0010 00000000 %?%?')

    def nextTrack(self):
        """
          Go to begining of next track.
        """
        self._trackChange(TRACK_NEXT)

    def previousTrack(self):
        """
          Go to begining of previous track.
        """
        self._trackChange(TRACK_PREVIOUS)

    def restartTrack(self):
        """
          Go to begining of current track.
        """
        self._trackChange(TRACK_RESTART)

    def eraseDisc(self):
        """
          Erase disc.
          This is reported not to check for any track protection, and
          unconditionaly earses everything.
        """
        # XXX: test to see if it honors read-only disc mode.
        query = self.formatQuery('1840 ff 0000')
        reply = self.send_query(query)
        self.scanQuery(reply, '1840 00 0000')

    def syncTOC(self):
        query = self.formatQuery('1808 10180200 00')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1808 10180200 00')

    def cacheTOC(self):
        query = self.formatQuery('1808 10180203 00')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1808 10180203 00')

    def getDiscFlags(self):
        """
          Get disc flags.
          Returns a bitfield (see DISC_FLAG_* constants).
        """
        query = self.formatQuery('1806 01101000 ff00 0001000b')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1806 01101000 1000 0001000b %b')[0]

    def getTrackCount(self):
        """
          Get the number of disc tracks.
        """
        query = self.formatQuery('1806 02101001 3000 1000 ff00 00000000')
        reply = self.send_query(query)
        data = self.scanQuery(reply, '1806 02101001 %?%? %?%? 1000 00%?0000 ' \
                              '%x')[0]
        assert len(data) == 6, len(data)
        assert data[:5] == '\x00\x10\x00\x02\x00', data[:5]
        return ord(data[5])

    def _getDiscTitle(self, wchar=False):
        # XXX: long title support untested.
        if wchar:
            wchar_value = 1
        else:
            wchar_value = 0
        done = 0
        remaining = 0
        total = 1
        result = []
        while done < total:
            query = self.formatQuery('1806 02201801 00%b 3000 0a00 ff00 %w%w',
                                     wchar_value, remaining, done)
            reply = self.send_query(query)
            if remaining == 0:
                chunk_size, total, chunk = self.scanQuery(reply,
                    '1806 02201801 00%? 3000 0a00 1000 %w0000 %?%?000a %w %*')
                chunk_size -= 6
            else:
                chunk_size, chunk = self.scanQuery(reply,
                    '1806 02201801 00%? 3000 0a00 1000 %w%?%? %*')
            assert chunk_size == len(chunk)
            result.append(chunk)
            done += chunk_size
            remaining = total - done
        #if not wchar and len(result):
        #    assert result[-1] == '\x00'
        #    result = result[:-1]
        return ''.join(result)

    def getDiscTitle(self, wchar=False):
        """
          Return disc title.
          wchar (bool)
            If True, return the content of wchar title.
            If False, return the ASCII title.
        """
        title = self._getDiscTitle(wchar=wchar)
        if title.endswith('//'):
            # this is a grouped minidisc which may have a disc title
            # The disc title is always stored in the first entry and
            # applied to the imaginary track 0
            firstentry = title.split('//')[0]
            if firstentry.startswith('0;'):
                title = firstentry[2:len(firstentry)];
            else:
                title = '';
        return title

    def getTrackGroupList(self):
        """
          Return a list representing track groups.
          This list is composed of 2-tuples:
            group title
            track number list
        """
        raw_title = self._getDiscTitle()
        group_list = raw_title.split('//')
        track_dict = {}
        track_count = self.getTrackCount()
        result = []
        append = result.append
        for group_index, group in enumerate(group_list):
            if group == '': # (only ?) last group might be delimited but empty.
                continue
            if group[0] == '0' or ';' not in group: # Disk title
                continue
            track_range, group_name = group.split(';', 1)
            if '-' in track_range:
                track_min, track_max = track_range.split('-')
            else:
                track_min = track_max = track_range
            track_min, track_max = int(track_min), int(track_max)
            assert 0 <= track_min <= track_max <= track_count, (
                track_min, track_max, track_count)
            track_list = []
            track_append = track_list.append
            for track in xrange(track_min - 1, track_max):
                if track in track_dict:
                    raise ValueError('Track %i is in 2 groups: %r[%i] & '
                         '%r[%i]' % (track, track_dict[track][0],
                         track_dict[track][1], group_name, group_index))
                track_dict[track] = group_name, group_index
                track_append(track)
            append((group_name, track_list))
        track_list = [x for x in xrange(track_count) if x not in track_dict]
        if len(track_list):
            append((None, track_list))
        return result

    def getTrackTitle(self, track, wchar=False):
        """
          Return track title.
          track (int)
            Track number.
          wchar (bool)
            If True, return the content of wchar title.
            If False, return the ASCII title.
        """
        if wchar:
            wchar_value = 3
        else:
            wchar_value = 2
        query = self.formatQuery('1806 022018%b %w 3000 0a00 ff00 00000000',
                                 wchar_value, track)
        reply = self.send_query(query)
        result = self.scanQuery(reply, '1806 022018%? %?%? %?%? %?%? 1000 ' \
                                '00%?0000 00%?000a %x')[0]
        #if not wchar and len(result):
        #    assert result[-1] == '\x00'
        #    result = result[:-1]
        return result

    def setDiscTitle(self, title, wchar=False):
        """
          Set disc title.
          title (str)
            The new title.
          wchar (bool)
            If True, return the content of wchar title.
            If False, return the ASCII title.
        """
        if wchar:
            wchar = 1
        else:
            wchar = 0
        old_len = len(self.getDiscTitle())
        query = self.formatQuery('1807 02201801 00%b 3000 0a00 5000 %w 0000 ' \
                                 '%w %s', wchar, len(title), old_len, title)
        reply = self.send_query(query)
        self.scanQuery(reply, '1807 02201801 00%? 3000 0a00 5000 %?%? 0000 ' \
                              '%?%?')

    def setTrackTitle(self, track, title, wchar=False):
        """
          Set track title.
          track (int)
            Track to retitle.
          title (str)
            The new title.
          wchar (bool)
            If True, return the content of wchar title.
            If False, return the ASCII title.
        """
        if wchar:
            wchar = 3
        else:
            wchar = 2
        try:
            old_len = len(self.getTrackTitle(track))
        except NetMDRejected:
            old_len = 0
        query = self.formatQuery('1807 022018%b %w 3000 0a00 5000 %w 0000 ' \
                                 '%w %*', wchar, track, len(title), old_len,
                                 title)
        reply = self.send_query(query)
        self.scanQuery(reply, '1807 022018%? %?%? 3000 0a00 5000 %?%? 0000 ' \
                              '%?%?')

    def eraseTrack(self, track):
        """
          Remove a track.
          track (int)
            Track to remove.
        """
        query = self.formatQuery('1840 ff01 00 201001 %w', track)
        reply = self.send_query(query)
        self.scanQuery(reply, '1840 1001 00 201001 %?%?')

    def moveTrack(self, source, dest):
        """
          Move a track.
          source (int)
            Track position before moving.
          dest (int)
            Track position after moving.
        """
        query = self.formatQuery('1843 ff00 00 201001 00 %w 201001 %w', source,
                                 dest)
        reply = self.send_query(query)
        self.scanQuery(reply, '1843 0000 00 201001 00 %?%? 201001 %?%?')

    def _getTrackInfo(self, track, p1, p2):
        query = self.formatQuery('1806 02201001 %w %w %w ff00 00000000', track,
                                 p1, p2)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1806 02201001 %?%? %?%? %?%? 1000 ' \
                              '00%?0000 %x')[0]

    def getTrackLength(self, track):
        """
          Get track duration.
          track (int)
            Track to fetch information from.
          Returns a list of 4 elements:
          - hours
          - minutes
          - seconds
          - samples (512 per second)
        """
        raw_value = self._getTrackInfo(track, 0x3000, 0x0100)
        result = self.scanQuery(raw_value, '0001 0006 0000 %b %b %b %b')
        result[0] = BCD2int(result[0])
        result[1] = BCD2int(result[1])
        result[2] = BCD2int(result[2])
        result[3] = BCD2int(result[3])
        return result

    def getTrackEncoding(self, track):
        """
          Get track encoding parameters.
          track (int)
            Track to fetch information from.
          Returns a list of 2 elements:
          - codec (see ENCODING_* constants)
          - channel number (see CHANNELS_* constants)
        """
        return self.scanQuery(self._getTrackInfo(track, 0x3080, 0x0700),
                              '8007 0004 0110 %b %b')

    def getTrackFlags(self, track):
        """
          Get track flags.
          track (int)
            Track to fetch information from.
          Returns a bitfield (See TRACK_FLAG_* constants).
        """
        query = self.formatQuery('1806 01201001 %w ff00 00010008', track)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1806 01201001 %?%? 10 00 00010008 %b') \
               [0]

    def getDiscCapacity(self):
        """
          Get disc capacity.
          Returns a list of 3 lists of 4 elements each (see getTrackLength).
          The first list is the recorded duration.
          The second list is the total disc duration (*).
          The third list is the available disc duration (*).
          (*): This result depends on current recording parameters.
        """
        query = self.formatQuery('1806 02101000 3080 0300 ff00 00000000')
        reply = self.send_query(query)
        raw_result = self.scanQuery(reply, '1806 02101000 3080 0300 1000 ' \
                                    '001d0000 001b 8003 0017 8000 0005 %w ' \
                                    '%b %b %b 0005 %w %b %b %b 0005 %w %b ' \
                                    '%b %b')
        result = []
        for offset in xrange(3):
            offset *= 4
            result.append([
                BCD2int(raw_result[offset + 0]),
                BCD2int(raw_result[offset + 1]),
                BCD2int(raw_result[offset + 2]),
                BCD2int(raw_result[offset + 3])])
        return result

    def getRecordingParameters(self):
        """
          Get the current recording parameters.
          See getTrackEncoding.
        """
        query = self.formatQuery('1809 8001 0330 8801 0030 8805 0030 8807 ' \
                                 '00 ff00 00000000')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1809 8001 0330 8801 0030 8805 0030 ' \
                              '8807 00 1000 000e0000 000c 8805 0008 80e0 ' \
                              '0110 %b %b 4000')

    def saveTrackToStream(self, track, outstream, events=defaultUploadEvents()):
        """
          Digitaly dump a track to file.
          This is only available on MZ-RH1.
          track (int)
            Track to extract.
          outfile_name (str)
            Path of file to save extracted data in.
        """
        track += 1
        query = self.formatQuery('1800 080046 f003010330 ff00 1001 %w', track)
        reply = self.send_query(query)
        (frames,codec,length) = self.scanQuery(reply, '1800 080046 f003010330 0000 1001 ' \
                                '%w %b %d')
        events.trackinfo(frames, length, codec);
        self.net_md.readBulkToFile(length, outstream, callback=events.progress)
        reply = self.readReply()
        self.scanQuery(reply, '1800 080046 f003010330 0000 1001 %?%? 0000')
        # Prevent firmware lockups on successive saveTrackToStream calls
        sleep(0.01)

    def disableNewTrackProtection(self, val):
        """
         NetMD downloaded tracks are usually protected from modification
         at the MD device to prevent loosing the check-out license. This
         setting can be changed on some later models to have them record
         unprotected tracks, like Simple Burner does.
         The setting stays in effect until endSecureSession, where it
         is reset to 0.
         val (int)
           zero enables protection of future downloaded tracks, one
           disables protection for these tracks.
        """
        query = self.formatQuery('1800 080046 f0030103 2b ff %w', val)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 2b 00 %?%?')

    def enterSecureSession(self):
        """
         Enter a session secured by a root key found in an EKB. The
         EKB for this session has to be download after entering the
         session.
        """
        query = self.formatQuery('1800 080046 f0030103 80 ff')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 80 00')

    def leaveSecureSession(self):
        """
         Forget the key material from the EKB used in the secure
         session.
        """
        query = self.formatQuery('1800 080046 f0030103 81 ff')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 81 00')

    def getLeafID(self):
        """
         Read the leaf ID of the present NetMD device. The leaf ID tells
         which keys the device posesses, which is needed to find out which
         parts of the EKB needs to be sent to the device for it to decrypt
         the root key.
         The leaf ID is a 8-byte constant
        """
        query = self.formatQuery('1800 080046 f0030103 11 ff')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 11 00 %*')[0]

    def sendKeyData(self, ekbid, keychain, depth, ekbsignature):
        """
         Send key data to the device. The device uses it's builtin key
         to decrypt the root key from an EKB.
         ekbid (int)
           The ID of the EKB.
         keychain (list of 16-byte str)
           A chain of encrypted keys. The one end of the chain is the
           encrypted root key, the other end is a key encrypted by a key
           the device has in it's key set. The direction of the chain is
           not yet known.
         depth (str)
           Selects which key from the devices keyset has to be used to
           start decrypting the chain. Each key in the key set corresponds
           to a specific depth in the tree of device IDs.
         ekbsignature
           A 24 byte signature of the root key. Used to verify integrity
           of the decrypted root key by the device.
        """
        chainlen = len(keychain)
        # 16 bytes header, 16 bytes per key, 24 bytes for the signature
        databytes = 16 + 16*chainlen + 24
        for key in keychain:
            if len(key) != 16:
                raise ValueError("Each key in the chain needs to have 16 bytes, this one has %d" % len(key))
        if depth < 1 or depth > 63:
            raise ValueError('Supplied depth is invalid')
        if len(ekbsignature) != 24:
            raise ValueError('Supplied EKB signature length wrong')
        query = self.formatQuery('1800 080046 f0030103 12 ff %w %d' \
                                 '%d %d %d 00000000 %* %*', databytes, databytes,
                                 chainlen, depth, ekbid, "".join(keychain), ekbsignature)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 12 01 %?%? %?%?%?%?')

    def sessionKeyExchange(self, hostnonce):
        """
         Exchange a session key with the device. Needs to have a root
         key sent to the device using sendKeyData before.
         hostnonce (str)
           8 bytes random binary data
         Returns
           device nonce (str), another 8 bytes random data
        """
        if len(hostnonce) != 8:
            raise ValueError('Supplied host nonce length wrong')
        query = self.formatQuery('1800 080046 f0030103 20 ff 000000 %*', hostnonce)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 20 00 000000 %*')[0]

    def sessionKeyForget(self):
        """
         Invalidate the session key established by nonce exchange.
         Does not invalidate the root key set up by sendKeyData.
        """
        query = self.formatQuery('1800 080046 f0030103 21 ff 000000')
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 21 00 000000')

    def setupDownload(self, contentid, keyenckey, sessionkey):
        """
         Prepare the download of a music track to the device.
         contentid (str)
           20 bytes Unique Identifier for the DRM system.
         keyenckey (str)
           8 bytes DES key used to encrypt the block data keys
         sessionkey (str)
           8 bytes DES key used for securing the current session, the key
           has to be calculated by the caller from the data exchanged in
           sessionKeyExchange and the root key selected by sendKeyData
        """
        if DES is None:
            raise ImportError('Crypto.Cypher.DES not found, you cannot '
                'download tracks')
        if len(contentid) != 20:
            raise ValueError('Supplied Content ID length wrong')
        if len(keyenckey) != 8:
            raise ValueError('Supplied Key Encryption Key length wrong')
        if len(sessionkey) != 8:
            raise ValueError('Supplied Session Key length wrong')
        encrypter = DES.new(sessionkey, DES.MODE_CBC, '\0\0\0\0\0\0\0\0')
        encryptedarg = encrypter.encrypt('\1\1\1\1' + contentid + keyenckey);
        query = self.formatQuery('1800 080046 f0030103 22 ff 0000 %*', encryptedarg)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 22 00 0000')

    def commitTrack(self, tracknum, sessionkey):
        """
         Commit a track. The idea is that this command tells the device
         that the license for the track has been checked out from the
         computer.
         track (int)
           Track number returned from downloading command
         sessionkey (str)
           8-byte DES key used for securing the download session
        """
        if DES is None:
            raise ImportError('Crypto.Cypher.DES not found, you cannot '
                'download tracks')
        if len(sessionkey) != 8:
            raise ValueError('Supplied Session Key length wrong')
        encrypter = DES.new(sessionkey, DES.MODE_ECB)
        authentication = encrypter.encrypt('\0\0\0\0\0\0\0\0')
        query = self.formatQuery('1800 080046 f0030103 48 ff 00 1001 %w %*',
                                 tracknum, authentication)
        reply = self.send_query(query)
        return self.scanQuery(reply, '1800 080046 f0030103 48 00 00 1001 %?%?')

    def sendTrack(self, wireformat, diskformat, frames, pktcount, packets, sessionkey):
        """
         Send a track to the NetMD unit.
         wireformat (int)
           The format of the data sent over the USB link.
           one of WIREFORMAT_PCM, WIREFORMAT_LP2, WIREFORMAT_105KBPS or
           WIREFORMAT_LP4
         diskformat (int)
           The format of the data on the MD medium.
           one of DISKFORMAT_SP_STEREO, DISKFORMAT_LP2 or DISKFORMAT_LP4.
         frames (int)
           The number of frames to transfer. The frame size depends on
           the wire format. It's 2048 bytes for WIREFORMAT_PCM, 192 bytes
           for WIREFORMAT_LP2, 152 bytes for WIREFORMAT_105KBPS and 92 bytes
           for WIREFORMAT_LP4.
         pktcount (int)
           Number of data packets to send (needed to calculate the raw
           packetized stream size
         packets (iterator)
           iterator over (str, str, str), with the first string being the
           encrypted DES encryption key for this packet (8 bytes), the second
           the IV (8 bytes, too) and the third string the encrypted data.
         sessionkey (str)
           8-byte DES key used for securing the download session
         Returns
           A tuple (tracknum, UUID, content ID).
           tracknum (int)
             the number the new track got.
           UUID (str)
             an 8-byte-value to recognize this track for check-in purpose
           content ID
             the content ID. Should always be the same as passed to 
             setupDownload, probably present to prevent some attack vectors
             to the DRM system.
        """
        if DES is None:
            raise ImportError('Crypto.Cypher.DES not found, you cannot '
                'download tracks')
        if len(sessionkey) != 8:
            raise ValueError('Supplied Session Key length wrong')
        framesizedict = {
            WIREFORMAT_PCM: 2048,
            WIREFORMAT_LP2: 192,
            WIREFORMAT_105KBPS: 152, 
            WIREFORMAT_LP4: 96,
        }
        totalbytes = framesizedict[wireformat] * frames + pktcount * 24;
        query = self.formatQuery('1800 080046 f0030103 28 ff 000100 1001' \
                                 'ffff 00 %b %b %d %d',
                                 wireformat, diskformat, frames, totalbytes)
        reply = self.send_query(query)
        self.scanQuery(reply, '1800 080046 f0030103 28 00 000100 1001 %?%? 00'\
                              '%*')
        for (key,iv,data) in packets:
            binpkt = pack('>Q',len(data)) + key + iv + data
            self.net_md.writeBulk(binpkt)
        reply = self.readReply()
        self.net_md._getReplyLength()
        (track, encryptedreply) = \
          self.scanQuery(reply, '1800 080046 f0030103 28 00 000100 1001 %w 00' \
                                '%?%? %?%?%?%? %?%?%?%? %*')
        encrypter = DES.new(sessionkey, DES.MODE_CBC, '\0\0\0\0\0\0\0\0')
        replydata = encrypter.decrypt(encryptedreply)
        return (track, replydata[0:8], replydata[12:32])

    def getTrackUUID(self, track):
        """
         Gets the DRM tracking ID for a track.
         NetMD downloaded tracks have an 8-byte identifier (instead of their
         content ID) stored on the MD medium. This is used to verify the
         identity of a track when checking in.
         track (int)
           The track number
         Returns
           An 8-byte binary string containing the track UUID.
        """
        query = self.formatQuery('1800 080046 f0030103 23 ff 1001 %w', track)
        reply = self.send_query(query)
        return self.scanQuery(reply,'1800 080046 f0030103 23 00 1001 %?%? %*')[0]

def retailmac(key, value, iv = 8*"\0"):
    if DES is None or DES3 is None:
        raise ImportError('Crypto.Cypher.DES or DES3 not found, you cannot '
            'download tracks')
    subkeyA = key[0:8]
    beginning = value[0:-8]
    end = value[-8:]
    step1crypt = DES.new(subkeyA, DES.MODE_CBC, iv)
    iv2 = step1crypt.encrypt(beginning)[-8:]
    step2crypt = DES3.new(key, DES3.MODE_CBC, iv2)
    return step2crypt.encrypt(end)

diskforwire = {
    WIREFORMAT_PCM: DISKFORMAT_SP_STEREO,
    WIREFORMAT_LP2: DISKFORMAT_LP2,
    WIREFORMAT_105KBPS: DISKFORMAT_LP2,
    WIREFORMAT_LP4: DISKFORMAT_LP4,
}


class MDSession:
    def __init__(self, md_iface, ekbobject):
        self.md = md_iface
        self.sessionkey = None
        self.md.enterSecureSession()
        (chain, depth, sig) = ekbobject.getEKBDataForLeafId(self.md.getLeafID())
        self.md.sendKeyData(ekbobject.getEKBID(), chain, depth, sig)
        hostnonce = array.array('B',[random.randrange(255) for x in range(8)]).tostring()
        devnonce = self.md.sessionKeyExchange(hostnonce)
        nonce = hostnonce + devnonce
        self.sessionkey = retailmac(ekbobject.getRootKey(), nonce)

    def downloadtrack(self, trk):
        self.md.setupDownload(trk.getContentID(), trk.getKEK(), self.sessionkey)
        dataformat = trk.getDataFormat()
        (track,uuid,ccid) = self.md.sendTrack(dataformat, diskforwire[dataformat], \
                                   trk.getFramecount(), trk.getPacketcount(),
                                   trk.getPackets(), self.sessionkey)
        self.md.cacheTOC()
        self.md.setTrackTitle(track,trk.getTitle())
        self.md.syncTOC()
        self.md.commitTrack(track, self.sessionkey)
        return (track, uuid, ccid)

    
    def __del__(self):
        self.close()

    def close(self):
        if self.sessionkey != None:
            self.md.sessionKeyForget
            self.sessionkey = None
        self.md.leaveSecureSession()

