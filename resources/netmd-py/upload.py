#!/usr/bin/python
import os
import usb1
import libnetmd
import string
from time import sleep
from struct import pack

RIFF_FORMAT_TAG_ATRAC3 = 0x270

def main(bus=None, device_address=None, track_range=None, output_path=None, sonicstage_nos=False):
    context = usb1.LibUSBContext()
    for md in libnetmd.iterdevices(context, bus=bus,
                                   device_address=device_address):
        md_iface = libnetmd.NetMDInterface(md)
        MDDump(md_iface, track_range, output_path, sonicstage_nos)

def getTrackList(md_iface, track_range):
    channel_count_dict = {
        libnetmd.CHANNELS_MONO: 1,
        libnetmd.CHANNELS_STEREO: 2,
    }
    result = []
    append = result.append
    track_count = md_iface.getTrackCount()
    if isinstance(track_range, tuple):
        min_track, max_track = track_range
        if max_track is None:
            max_track = track_count - 1
        assert max_track < track_count
        assert min_track < track_count
        track_list = xrange(min_track, max_track + 1)
    elif isinstance(track_range, int):
        assert track_range < track_count
        track_list = [track_range]
    else:
        track_list = xrange(track_count)
    for track in track_list:
        flags = md_iface.getTrackFlags(track)
        codec, channel_count = md_iface.getTrackEncoding(track)
        if flags != libnetmd.TRACK_FLAG_PROTECTED:
            channel_count = libnetmd.CHANNEL_COUNT_DICT[channel_count]
            ascii_title = md_iface.getTrackTitle(track)
            wchar_title = md_iface.getTrackTitle(track, True).decode('shift_jis')
            title = wchar_title or ascii_title
            append((track, codec,
                    channel_count,
                    title))
    return result

def formatAeaHeader(name = '', channels = 2, soundgroups = 1, groupstart = 0, encrypted = 0, flags=[0,0,0,0,0,0,0,0]):
    return pack("2048s", # pad to header size
                pack("<I256siBx8IIII"
                                      ,2048,   # header size
                                      name,
                                      soundgroups,
                                      channels,
                                      flags[0],flags[1],flags[2],flags[3],
                                      flags[4],flags[5],flags[6],flags[7],
                                      0,      # Should be time of recordin in
                                              # 32 bit DOS format.
                                      encrypted,
                                      groupstart
                                      ))

class aeaUploadEvents(libnetmd.defaultUploadEvents):
    def __init__(self, stream, channels, name):
        self.stream = stream
        self.channels = channels
        self.name = name

    def trackinfo(self, frames, bytes, format):
        maskedformat = format & 0x06;
        if not ((maskedformat == libnetmd.DISKFORMAT_SP_STEREO and self.channels == 2) or \
                (maskedformat == libnetmd.DISKFORMAT_SP_MONO   and self.channels == 1)):
            raise ValueError, 'Unexpected format byte %02x for %d channels' % \
                                 (format, self.channels)
        self.stream.write(formatAeaHeader(name = self.name, soundgroups=frames, channels=self.channels))
        libnetmd.defaultUploadEvents.trackinfo(self, frames, bytes, format)

# LP2/LP4 is always stereo on minidisc.
def formatWavHeader(format, bytes):
    maskedformat = format & 0x06;
    if maskedformat == libnetmd.DISKFORMAT_LP4:
        bytesperframe = 96
        jointstereo = 1
    elif maskedformat == libnetmd.DISKFORMAT_LP2:
        bytesperframe = 192
        jointstereo = 0
    else:
        raise ValueError, 'unexpected format byte %02x' % format
    bytespersecond = bytesperframe * 44100 / 512
    return pack("<4sI4s"     # "RIFF" header
                "4sIHHIIHH"  # "fmt " chunk - standard part
                "HHIHHHH"    # "fmt " chunk - ATRAC extension
                "4sI",       # "data" chunk header

                'RIFF', bytes+60, 'WAVE',

                'fmt ',32, RIFF_FORMAT_TAG_ATRAC3, 2, 44100,
                bytespersecond, 2 * bytesperframe, 0,

                14, 1, bytesperframe, jointstereo, jointstereo, 1, 0,

                'data', bytes)

# This creates an ffmpeg compatible WAV header.
class wavUploadEvents(libnetmd.defaultUploadEvents):
    def __init__(self, stream):
        self.stream = stream

    def trackinfo(self, frames, bytes, format):
        print 'Format byte', format
        # RIFF header
        self.stream.write(formatWavHeader(format, bytes))
        libnetmd.defaultUploadEvents.trackinfo(self, frames, bytes, format)

def MDDump(md_iface, track_range, output_path, sonicstage_nos):
    ascii_title = md_iface.getDiscTitle()
    wchar_title = md_iface.getDiscTitle(True).decode('shift_jis')
    disc_title = wchar_title or ascii_title
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    if output_path is not None:
        directory = output_path
    else:
        directory = "."
    if disc_title != '':
        directory += ''.join(c for c in disc_title if c in valid_chars);
    print 'Storing in', directory
    if not os.path.exists(directory):
        os.mkdir(directory)
    for track, codec, channels, title in \
        getTrackList(md_iface, track_range):

        if codec == libnetmd.ENCODING_SP:
            extension = 'aea'
        else:
            extension = 'at3'
        if sonicstage_nos:
            # write track numbers in the same format as when uploading from sonicstage
            filename = '%s/%03i-%s.%s' % (directory, track + 1, ''.join(c for c in title if c in valid_chars), extension)
        else:
            # write traditional upload.py song numbers
            filename = '%s/%02i - %s.%s' % (directory, track + 1, ''.join(c for c in title if c in valid_chars), extension)
        print 'Uploading', filename
        with open(filename,"wb") as aeafile:
            if codec == libnetmd.ENCODING_SP:
                md_iface.saveTrackToStream(track, aeafile,events=aeaUploadEvents(aeafile, channels, title))
            else:
                md_iface.saveTrackToStream(track, aeafile,events=wavUploadEvents(aeafile))
            print "Wrote: %s" % filename

    # TODO: generate playlists based on groups defined on the MD
    print 'Finished.'

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-b', '--bus')
    parser.add_option('-d', '--device')
    parser.add_option('-t', '--track-range')
    parser.add_option('-o', '--output-path')
    parser.add_option("-s", "--sonicstage-nos",
                  action="store_true", default=False,
                  help="Use SonicStage style track numbering not traditional upload.py")
    (options, args) = parser.parse_args()
    assert len(args) < 3
    track_range = options.track_range
    if track_range is not None:
        if '-' in track_range:
            begin, end = track_range.split('-', 1)
            if begin == '':
                begin = 0
            else:
                begin = int(begin) - 1
            if end == '':
                end = None
            else:
                end = int(end) - 1
                assert begin < end
            track_range = (begin, end)
        else:
            track_range = int(track_range) - 1
    main(bus=options.bus, device_address=options.device,
         track_range=track_range, output_path=options.output_path, sonicstage_nos=options.sonicstage_nos)
