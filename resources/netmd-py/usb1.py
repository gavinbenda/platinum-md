"""
Pythonic wrapper for libusb-1.0.

The first thing you must do is to get an "USB context". To do so, create a
LibUSBContext instance.
Then, you can use it to browse available USB devices and open the one you want
to talk to.
At this point, you should have a USBDeviceHandle instance (as returned by
LibUSBContext or USBDevice instances), and you can start exchanging with the
device.

Features:
- Basic device settings (configuration & interface selection, ...)
- String descriptor lookups (ASCII & unicode), and list supported language
  codes
- Synchronous I/O (control, bulk, interrupt)
- Asynchronous I/O (control, bulk, interrupt, isochronous)
  Note: Isochronous support is experimental.
  See USBPoller, USBTransfer and USBTransferHelper.
"""

import libusb1
from ctypes import byref, create_string_buffer, c_int, sizeof, POINTER, \
    create_unicode_buffer, c_wchar, cast, c_uint16, c_ubyte, string_at, \
    addressof, c_void_p, cdll
from cStringIO import StringIO
import sys
from ctypes.util import find_library

__all__ = ['LibUSBContext', 'USBDeviceHandle', 'USBDevice',
    'USBPoller', 'USBTransfer', 'USBTransferHelper', 'EVENT_CALLBACK_SET']

if sys.version_info[:2] >= (2, 6):
    if sys.platform == 'win32':
        from ctypes import get_last_error as get_errno
    else:
        from ctypes import get_errno
else:
    def get_errno():
        raise NotImplementedError("Your python version doesn't support "
            "errno/last_error")

__libc_name = find_library('c')
if __libc_name is None:
    # Of course, will leak memory.
    # Should we warn user ? How ?
    _free = lambda x: None
else:
    _free = getattr(cdll, __libc_name).free
del __libc_name

# Default string length
# From a comment in libusb-1.0: "Some devices choke on size > 255"
STRING_LENGTH = 255

EVENT_CALLBACK_SET = frozenset((
    libusb1.LIBUSB_TRANSFER_COMPLETED,
    libusb1.LIBUSB_TRANSFER_ERROR,
    libusb1.LIBUSB_TRANSFER_TIMED_OUT,
    libusb1.LIBUSB_TRANSFER_CANCELLED,
    libusb1.LIBUSB_TRANSFER_STALL,
    libusb1.LIBUSB_TRANSFER_NO_DEVICE,
    libusb1.LIBUSB_TRANSFER_OVERFLOW,
))

DEFAULT_ASYNC_TRANSFER_ERROR_CALLBACK = lambda x: False

def create_binary_buffer(string_or_len):
    # Prevent ctypes from adding a trailing null char.
    if isinstance(string_or_len, basestring):
        result = create_string_buffer(string_or_len, len(string_or_len))
    else:
        result = create_string_buffer(string_or_len)
    return result

class USBTransfer(object):
    """
    USB asynchronous transfer control & data.

    All modification methods will raise if called on a submitted transfer.
    Methods noted as "should not be called on a submitted transfer" will not
    prevent you from reading, but returned value is unspecified.
    """
    # Prevent garbage collector from freeing the free function before our
    # instances, as we need it to property destruct them.
    __libusb_free_transfer = libusb1.libusb_free_transfer
    __libusb_cancel_transfer = libusb1.libusb_cancel_transfer
    __USBError = libusb1.USBError
    __LIBUSB_ERROR_NOT_FOUND = libusb1.LIBUSB_ERROR_NOT_FOUND
    __transfer = None
    __initialized = False
    __submitted = False
    __callback = None
    __ctypesCallbackWrapper = None

    def __init__(self, handle, iso_packets=0):
        """
        You should not instanciate this class directly.
        Call "getTransfer" method on an USBDeviceHandle instance to get
        instances of this class.
        """
        if iso_packets < 0:
            raise ValueError('Cannot request a negative number of iso '
                'packets.')
        self.__handle = handle
        self.__num_iso_packets = iso_packets
        result = libusb1.libusb_alloc_transfer(iso_packets)
        if not result:
            raise libusb1.USBError('Unable to get a transfer object')
        self.__transfer = result
        self.__ctypesCallbackWrapper = libusb1.libusb_transfer_cb_fn_p(
            self.__callbackWrapper)

    def close(self):
        """
        Stop using this transfer.
        This removes some references to other python objects, to help garbage
        collection.
        Raises if called on a submitted transfer.
        This does not prevent future reuse of instance (calling one of
        "setControl", "setBulk", "setInterrupt" or "setIsochronous" methods
        will initialize it properly again), just makes it ready to be
        garbage-collected.
        It is not mandatory to call it either, if you have no problems with
        garbage collection.
        """
        if self.__submitted:
            raise ValueError('Cannot close a submitted transfer')
        self.__initialized = False
        self.__callback = None

    def __del__(self):
        if self.__transfer is not None:
            try:
                # If this doesn't raise, we're doomed; transfer was submitted,
                # still python decided to garbage-collect this instance.
                # Stick to libusb's documentation, and don't free the
                # transfer. If interpreter is shutting down, kernel will
                # reclaim memory anyway.
                # Note: we can't prevent transfer's buffer from being
                # garbage-collected as soon as there will be no remaining
                # reference to transfer, so a segfault might happen anyway.
                # Should we warn user ? How ?
                self.cancel()
            except self.__USBError, exception:
                if exception.value == self.__LIBUSB_ERROR_NOT_FOUND:
                    # Transfer was not submitted, we can free it.
                    self.__libusb_free_transfer(self.__transfer)
                else:
                    raise

    def __callbackWrapper(self, transfer_p):
        """
        Makes it possible for user-provided callback to alter transfer when
        fired (ie, mark transfer as not submitted upon call).
        """
        mine = addressof(self.__transfer.contents)
        his = addressof(transfer_p.contents)
        assert mine == his, (mine, his)
        self.__submitted = False
        callback = self.__callback
        if callback is not None:
            callback(self)

    def setCallback(self, callback):
        """
        Change transfer's callback.
        """
        if self.__submitted:
            raise ValueError('Cannot alter a submitted transfer')
        self.__callback = callback

    def getCallback(self):
        """
        Get currently set callback.
        """
        return self.__callback

    def setControl(self, request_type, request, value, index, buffer_or_len,
            callback=None, user_data=None, timeout=0):
        """
        Setup transfer for control use.

        request_type, request, value, index: See USBDeviceHandle.controlWrite.
        buffer_or_len: either a string (when sending data), or expected data
          length (when receiving data)
        callback: function to call upon event. Called with transfer as
          parameter, return value ignored.
        user_data: to pass some data to/from callback
        timeout: in milliseconds, how long to wait for devices acknowledgement
          or data. Set to 0 to disable.
        """
        if self.__submitted:
            raise ValueError('Cannot alter a submitted transfer')
        if isinstance(buffer_or_len, basestring):
            length = len(buffer_or_len)
            string_buffer = create_binary_buffer(
                ' ' * libusb1.LIBUSB_CONTROL_SETUP_SIZE + buffer_or_len)
        else:
            length = buffer_or_len
            string_buffer = create_binary_buffer(length + \
                libusb1.LIBUSB_CONTROL_SETUP_SIZE)
        self.__initialized = False
        libusb1.libusb_fill_control_setup(string_buffer, request_type,
            request, value, index, length)
        libusb1.libusb_fill_control_transfer(self.__transfer, self.__handle,
            string_buffer, self.__ctypesCallbackWrapper, user_data, timeout)
        self.__callback = callback
        self.__initialized = True

    def setBulk(self, endpoint, buffer_or_len, callback=None, user_data=None,
            timeout=0):
        """
        Setup transfer for bulk use.

        endpoint: endpoint to submit transfer to (implicitly sets transfer
          direction).
        buffer_or_len: either a string (when sending data), or expected data
          length (when receiving data)
        callback: function to call upon event. Called with transfer as
          parameter, return value ignored.
        user_data: to pass some data to/from callback
        timeout: in milliseconds, how long to wait for devices acknowledgement
          or data. Set to 0 to disable.
        """
        if self.__submitted:
            raise ValueError('Cannot alter a submitted transfer')
        string_buffer = create_binary_buffer(buffer_or_len)
        self.__initialized = False
        libusb1.libusb_fill_bulk_transfer(self.__transfer, self.__handle,
            endpoint, string_buffer, sizeof(string_buffer),
            self.__ctypesCallbackWrapper, user_data, timeout)
        self.__callback = callback
        self.__initialized = True

    def setInterrupt(self, endpoint, buffer_or_len, callback=None,
            user_data=None, timeout=0):
        """
        Setup transfer for interrupt use.

        endpoint: endpoint to submit transfer to (implicitly sets transfer
          direction).
        buffer_or_len: either a string (when sending data), or expected data
          length (when receiving data)
        callback: function to call upon event. Called with transfer as
          parameter, return value ignored.
        user_data: to pass some data to/from callback
        timeout: in milliseconds, how long to wait for devices acknowledgement
          or data. Set to 0 to disable.
        """
        if self.__submitted:
            raise ValueError('Cannot alter a submitted transfer')
        string_buffer = create_binary_buffer(buffer_or_len)
        self.__initialized = False
        libusb1.libusb_fill_interrupt_transfer(self.__transfer, self.__handle,
            endpoint, string_buffer,  sizeof(string_buffer),
            self.__ctypesCallbackWrapper, user_data, timeout)
        self.__callback = callback
        self.__initialized = True

    def setIsochronous(self, endpoint, buffer_or_len, callback=None,
            user_data=None, timeout=0, iso_transfer_length_list=None):
        """
        Setup transfer for isochronous use.

        endpoint: endpoint to submit transfer to (implicitly sets transfer
          direction).
        buffer_or_len: either a string (when sending data), or expected data
          length (when receiving data)
        callback: function to call upon event. Called with transfer as
          parameter, return value ignored.
        user_data: to pass some data to/from callback
        timeout: in milliseconds, how long to wait for devices acknowledgement
          or data. Set to 0 to disable.
        iso_transfer_length_list: list of individual transfer sizes. If not
          provided, buffer_or_len's size will be divided evenly among the
          number of ISO transfers given to receive current instance, rounded
          down. Providing a list allows overriding this (both the number of
          ISO transfers and their individual lengths).
        """
        if self.__submitted:
            raise ValueError('Cannot alter a submitted transfer')
        num_iso_packets = self.__num_iso_packets
        if num_iso_packets == 0:
            raise TypeError('This transfer canot be used for isochronous I/O. '
                'You must get another one with a non-zero iso_packets '
                'parameter.')
        string_buffer = create_binary_buffer(buffer_or_len)
        buffer_length = sizeof(string_buffer)
        if iso_transfer_length_list is None:
            iso_length = buffer_length / num_iso_packets
            iso_transfer_length_list = [iso_length for _ in
                xrange(num_iso_packets)]
        configured_iso_packets = len(iso_transfer_length_list)
        if configured_iso_packets > num_iso_packets:
            raise ValueError('Too many ISO transfer lengths (%i), there are '
                'only %i ISO transfers available' % (configured_iso_packets,
                    num_iso_packets))
        if sum(iso_transfer_length_list) > buffer_length:
            raise ValueError('ISO transfers too long (%i), there are only '
                '%i bytes available' % (sum(iso_transfer_length_list),
                    buffer_length))
        transfer_p = self.__transfer
        self.__initialized = False
        libusb1.libusb_fill_iso_transfer(transfer_p, self.__handle,
            endpoint, string_buffer, buffer_length, num_iso_packets,
            self.__ctypesCallbackWrapper, user_data, timeout)
        for length, iso_packet_desc in zip(iso_transfer_length_list,
                libusb1.get_iso_packet_list(transfer_p)):
            if length <= 0:
                raise ValueError('Negative/null transfer length are not '
                    'possible.')
            iso_packet_desc.length = length
        self.__callback = callback
        self.__initialized = True

    def getType(self):
        """
        Get transfer type.
        See libusb1.libusb_transfer_type.
        """
        return self.__transfer.contents.type

    def getEndpoint(self):
        """
        Get endpoint.
        """
        return self.__transfer.contents.endpoint

    def getStatus(self):
        """
        Get transfer status.
        Should not be called on a submitted transfer.
        """
        return self.__transfer.contents.status

    def getActualLength(self):
        """
        Get actually transfered data length.
        Should not be called on a submitted transfer.
        """
        return self.__transfer.contents.actual_length

    def getBuffer(self):
        """
        Get data buffer content.
        Should not be called on a submitted transfer.
        """
        transfer_p = self.__transfer
        transfer = transfer_p.contents
        if transfer.type == libusb1.LIBUSB_TRANSFER_TYPE_CONTROL:
            result = libusb1.libusb_control_transfer_get_data(transfer_p)
        else:
            result = string_at(transfer.buffer, transfer.length)
        return result

    def getISOBufferList(self):
        """
        Get individual ISO transfer's buffer.
        Returns a list with one item per ISO transfer, with their
        individually-configured sizes.
        Should not be called on a submitted transfer.
        """
        transfer_p = self.__transfer
        transfer = transfer_p.contents
        if transfer.type != libusb1.LIBUSB_TRANSFER_TYPE_ISOCHRONOUS:
            raise TypeError('This method cannot be called on non-iso '
                'transfers.')
        return libusb1.get_iso_packet_buffer_list(transfer_p)

    def getISOSetupList(self):
        """
        Get individual ISO transfer's setup.
        Returns a list of dicts, each containing an individual ISO transfer
        parameters:
        - length
        - actual_length
        - status
        (see libusb1's API documentation for their signification)
        Should not be called on a submitted transfer (except for 'length'
        values).
        """
        transfer_p = self.__transfer
        transfer = transfer_p.contents
        if transfer.type != libusb1.LIBUSB_TRANSFER_TYPE_ISOCHRONOUS:
            raise TypeError('This method cannot be called on non-iso '
                'transfers.')
        return [{
                'length': x.length,
                'actual_length': x.actual_length,
                'status': x.status,
            } for x in libusb1.get_iso_packet_list(transfer_p)]

    def setBuffer(self, buffer_or_len):
        """
        Replace buffer with a new one.
        Allows resizing read buffer and replacing data sent.
        Note: resizing is not allowed for isochornous buffer (use
        setIsochronous).
        """
        if self.__submitted:
            raise ValueError('Cannot alter a submitted transfer')
        transfer = self.__transfer.contents
        if transfer.type == libusb1.LIBUSB_TRANSFER_TYPE_CONTROL:
            raise ValueError('To alter control transfer buffer, use '
                'setControl')
        buff = create_binary_buffer(buffer_or_len)
        if transfer.type == libusb1.LIBUSB_TRANSFER_TYPE_ISOCHRONOUS and \
                sizeof(buff) != transfer.length:
            raise ValueError('To alter isochronous transfer buffer length, '
                'use setIsochronous')
        transfer.buffer = cast(buff, c_void_p)
        transfer.length = sizeof(buff)

    def isSubmitted(self):
        """
        Tells if this transfer is submitted and still pending.
        """
        return self.__submitted

    def submit(self):
        """
        Submit transfer for asynchronous handling.
        """
        if self.__submitted:
            raise ValueError('Cannot submit a submitted transfer')
        if not self.__initialized:
            raise ValueError('Cannot submit a transfer until it has been '
                'initialized')
        self.__submitted = True
        result = libusb1.libusb_submit_transfer(self.__transfer)
        if result:
            self.__submitted = False
            raise libusb1.USBError(result)

    def cancel(self):
        """
        Cancel transfer.
        Note: cancellation happens asynchronously, so you must wait for
        LIBUSB_TRANSFER_CANCELLED.
        """
        result = self.__libusb_cancel_transfer(self.__transfer)
        if result:
            raise self.__USBError(result)
        self.__submitted = False

class USBTransferHelper(object):
    """
    Simplifies subscribing to the same transfer over and over, and callback
    handling:
    - no need to read event status to execute apropriate code, just setup
      different functions for each status code
    - just return True instead of calling submit

    Callbacks used in this class must follow the callback API described in
    USBTransfer, and are expected to return a boolean:
    - True if transfer is to be submitted again (to receive/send more data)
    - False otherwise
    """
    # TODO: handle the special case of isochronous transfers, where there is a
    # global status and per-packet status.
    def __init__(self, transfer=None):
        """
        Create a transfer callback dispatcher.

        transfer parameter is deprecated. If provided, it will be equivalent
        to:
            helper = USBTransferHelper()
            transfer.setCallback(helper)
        and also allows using deprecated methods on this class (otherwise,
        they raise AttributeError).
        """
        if transfer is not None:
            # Deprecated: to drop
            self.__transfer = transfer
            transfer.setCallback(self)
        self.__event_callback_dict = {}
        self.__errorCallback = DEFAULT_ASYNC_TRANSFER_ERROR_CALLBACK

    def submit(self):
        """
        Submit the asynchronous read request.
        Deprecated. Use submit on transfer.
        """
        # Deprecated: to drop
        self.__transfer.submit()

    def cancel(self):
        """
        Cancel a pending read request.
        Deprecated. Use cancel on transfer.
        """
        # Deprecated: to drop
        self.__transfer.cancel()

    def setEventCallback(self, event, callback):
        """
        Set a function to call for a given event.
        Possible event identifiers are listed in EVENT_CALLBACK_SET.
        """
        if event not in EVENT_CALLBACK_SET:
            raise ValueError('Unknown event %r.' % (event, ))
        self.__event_callback_dict[event] = callback

    def setDefaultCallback(self, callback):
        """
        Set the function to call for event which don't have a specific callback
        registered.
        The initial default callback does nothing and returns False.
        """
        self.__errorCallback = callback

    def getEventCallback(self, event, default=None):
        """
        Return the function registered to be called for given event identifier.
        """
        return self.__event_callback_dict.get(event, default)

    def __call__(self, transfer):
        """
        Callback to set on transfers.
        """
        if self.getEventCallback(transfer.getStatus(), self.__errorCallback)(
                transfer):
            transfer.submit()

    def isSubmited(self):
        """
        Returns whether this reader is currently waiting for an event.
        Deprecatd. Use isSubmitted on transfer.
        """
        # Deprecated: to drop
        return self.__transfer.isSubmitted()

class USBPoller(object):
    """
    Class allowing integration of USB event polling in a file-descriptor
    monitoring event loop.
    """
    def __init__(self, context, poller):
        """
        Create a poller for given context.
        Warning: it will not check if another poller instance was already
        present for that context, and will replace it.

        poller is a polling instance implementing the following methods:
        - register(fd, event_flags)
          event_flags have the same meaning as in poll API (POLLIN & POLLOUT)
        - unregister(fd)
        - poll(timeout)
          timeout being a float in seconds, or None if there is no timeout.
          It must return a list of (descriptor, event) pairs.
        Note: USBPoller is itself a valid poller.
        """
        self.__context = context
        self.__poller = poller
        self.__fd_set = set()
        context.setPollFDNotifiers(self._registerFD, self._unregisterFD)
        for fd, events in context.getPollFDList():
            self._registerFD(fd, events)

    def __del__(self):
        self.__context.setPollFDNotifiers(None, None)

    def poll(self, timeout=None):
        """
        Poll for events.
        timeout can be a float in seconds, or None for no timeout.
        Returns a list of (descriptor, event) pairs.
        """
        next_usb_timeout = self.__context.getNextTimeout()
        if timeout is None:
            usb_timeout = next_usb_timeout
        elif next_usb_timeout:
            usb_timeout = min(next_usb_timeout, timeout)
        else:
            usb_timeout = timeout
        event_list = self.__poller.poll(usb_timeout)
        if event_list:
            fd_set = self.__fd_set
            result = [(x, y) for x, y in event_list if x not in fd_set]
            if len(result) != len(event_list):
                self.__context.handleEventsTimeout()
        else:
            result = event_list
            self.__context.handleEventsTimeout()
        return result

    def register(self, fd, events):
        """
        Register an USB-unrelated fd to poller.
        Convenience method.
        """
        if fd in self.__fd_set:
            raise ValueError('This fd is a special USB event fd, it cannot '
                'be polled.')
        self.__poller.register(fd, events)

    def unregister(self, fd):
        """
        Unregister an USB-unrelated fd from poller.
        Convenience method.
        """
        if fd in self.__fd_set:
            raise ValueError('This fd is a special USB event fd, it must '
                'stay registered.')
        self.__poller.unregister(fd)

    def _registerFD(self, fd, events, user_data=None):
        self.register(fd, events)
        self.__fd_set.add(fd)

    def _unregisterFD(self, fd, user_data=None):
        self.__fd_set.discard(fd)
        self.unregister(fd)

class USBDeviceHandle(object):
    """
    Represents an opened USB device.
    """
    __handle = None
    __libusb_close = libusb1.libusb_close

    def __init__(self, context, handle):
        """
        You should not instanciate this class directly.
        Call "open" method on an USBDevice instance to get an USBDeviceHandle
        instance.
        """
        # XXX Context parameter is just here as a hint for garbage collector:
        # It must collect USBDeviceHandle instance before their LibUSBContext.
        self.__context = context
        self.__handle = handle

    def __del__(self):
        self.close()

    def close(self):
        """
        Close this handle. If not called explicitely, will be called by
        destructor.
        """
        handle = self.__handle
        if handle is not None:
            self.__libusb_close(handle)
            self.__handle = None

    def getConfiguration(self):
        """
        Get the current configuration number for this device.
        """
        configuration = c_int()
        result = libusb1.libusb_get_configuration(self.__handle,
                                                  byref(configuration))
        if result:
            raise libusb1.USBError(result)
        return configuration

    def setConfiguration(self, configuration):
        """
        Set the configuration number for this device.
        """
        result = libusb1.libusb_set_configuration(self.__handle, configuration)
        if result:
            raise libusb1.USBError(result)

    def claimInterface(self, interface):
        """
        Claim (= get exclusive access to) given interface number. Required to
        receive/send data.
        """
        result = libusb1.libusb_claim_interface(self.__handle, interface)
        if result:
            raise libusb1.USBError(result)

    def releaseInterface(self, interface):
        """
        Release interface, allowing another process to use it.
        """
        result = libusb1.libusb_release_interface(self.__handle, interface)
        if result:
            raise libusb1.USBError(result)

    def setInterfaceAltSetting(self, interface, alt_setting):
        """
        Set interface's alternative setting (both parameters are integers).
        """
        result = libusb1.libusb_set_interface_alt_setting(self.__handle,
                                                          interface,
                                                          alt_setting)
        if result:
            raise libusb1.USBError(result)

    def clearHalt(self, endpoint):
        """
        Clear a halt state on given endpoint number.
        """
        result = libusb1.libusb_clear_halt(self.__handle, endpoint)
        if result:
            raise libusb1.USBError(result)

    def resetDevice(self):
        """
        Reinitialise current device.
        Attempts to restore current configuration & alt settings.
        If this fails, will result in a device diconnect & reconnect, so you
        have to close current device and rediscover it (notified by a
        LIBUSB_ERROR_NOT_FOUND error code).
        """
        result = libusb1.libusb_reset_device(self.__handle)
        if result:
            raise libusb1.USBError(result)

    def kernelDriverActive(self, interface):
        """
        Tell whether a kernel driver is active on given interface number.
        """
        result = libusb1.libusb_kernel_driver_active(self.__handle, interface)
        if result == 0:
            is_active = False
        elif result == 1:
            is_active = True
        else:
            raise libusb1.USBError(result)
        return is_active

    def detachKernelDriver(self, interface):
        """
        Ask kernel driver to detach from given interface number.
        """
        result = libusb1.libusb_detach_kernel_driver(self.__handle, interface)
        if result:
            raise libusb1.USBError(result)

    def attachKernelDriver(self, interface):
        """
        Ask kernel driver to re-attach to given interface number.
        """
        result = libusb1.libusb_attach_kernel_driver(self.__handle, interface)
        if result:
            raise libusb1.USBError(result)

    def getSupportedLanguageList(self):
        """
        Return a list of USB language identifiers (as integers) supported by
        current device for its string descriptors.
        """
        descriptor_string = create_binary_buffer(STRING_LENGTH)
        result = libusb1.libusb_get_string_descriptor(self.__handle,
            0, 0, descriptor_string, sizeof(descriptor_string))
        if result < 0:
            if result == libusb1.LIBUSB_ERROR_PIPE:
                # From libusb_control_transfer doc:
                # control request not supported by the device
                return []
            raise libusb1.USBError(result)
        length = cast(descriptor_string, POINTER(c_ubyte))[0]
        langid_list = cast(descriptor_string, POINTER(c_uint16))
        result = []
        append = result.append
        for offset in xrange(1, length / 2):
            append(libusb1.libusb_le16_to_cpu(langid_list[offset]))
        return result

    def getStringDescriptor(self, descriptor, lang_id):
        """
        Fetch description string for given descriptor and in given language.
        Use getSupportedLanguageList to know which languages are available.
        Return value is an unicode string.
        Return None if there is no such descriptor on device.
        """
        descriptor_string = create_unicode_buffer(
            STRING_LENGTH / sizeof(c_wchar))
        result = libusb1.libusb_get_string_descriptor(self.__handle,
            descriptor, lang_id, descriptor_string, sizeof(descriptor_string))
        if result == libusb1.LIBUSB_ERROR_NOT_FOUND:
            return None
        if result < 0:
            raise libusb1.USBError(result)
        return descriptor_string.value

    def getASCIIStringDescriptor(self, descriptor):
        """
        Fetch description string for given descriptor in first available
        language.
        Return value is an ASCII string.
        Return None if there is no such descriptor on device.
        """
        descriptor_string = create_binary_buffer(STRING_LENGTH)
        result = libusb1.libusb_get_string_descriptor_ascii(self.__handle,
             descriptor, descriptor_string, sizeof(descriptor_string))
        if result == libusb1.LIBUSB_ERROR_NOT_FOUND:
            return None
        if result < 0:
            raise libusb1.USBError(result)
        return descriptor_string.value

    # Sync I/O

    def _controlTransfer(self, request_type, request, value, index, data,
                         length, timeout):
        result = libusb1.libusb_control_transfer(self.__handle, request_type,
            request, value, index, data, length, timeout)
        if result < 0:
            raise libusb1.USBError(result)
        return result

    def controlWrite(self, request_type, request, value, index, data,
                     timeout=0):
        """
        Synchronous control write.
        request_type: request type bitmask (bmRequestType), see libusb1
          constants LIBUSB_TYPE_* and LIBUSB_RECIPIENT_*.
        request: request id (some values are standard).
        value, index, data: meaning is request-dependent.
        timeout: in milliseconds, how long to wait for device acknowledgement.
          Set to 0 to disable.

        Returns the number of bytes actually sent.
        """
        request_type = (request_type & ~libusb1.USB_ENDPOINT_DIR_MASK) | \
                        libusb1.LIBUSB_ENDPOINT_OUT
        data = create_binary_buffer(data)
        return self._controlTransfer(request_type, request, value, index, data,
                                     sizeof(data), timeout)

    def controlRead(self, request_type, request, value, index, length,
                    timeout=0):
        """
        Synchronous control read.
        timeout: in milliseconds, how long to wait for data. Set to 0 to
          disable.
        See controlWrite for other parameters description.

        Returns received data.
        """
        request_type = (request_type & ~libusb1.USB_ENDPOINT_DIR_MASK) | \
                        libusb1.LIBUSB_ENDPOINT_IN
        data = create_binary_buffer(length)
        transferred = self._controlTransfer(request_type, request, value,
                                            index, data, length, timeout)
        return data.raw[:transferred]

    def _bulkTransfer(self, endpoint, data, length, timeout):
        transferred = c_int()
        result = libusb1.libusb_bulk_transfer(self.__handle, endpoint,
            data, length, byref(transferred), timeout)
        if result:
            raise libusb1.USBError(result)
        return transferred.value

    def bulkWrite(self, endpoint, data, timeout=0):
        """
        Synchronous bulk write.
        endpoint: endpoint to send data to.
        data: data to send.
        timeout: in milliseconds, how long to wait for device acknowledgement.
          Set to 0 to disable.

        Returns the number of bytes actually sent.
        """
        endpoint = (endpoint & ~libusb1.USB_ENDPOINT_DIR_MASK) | \
                    libusb1.LIBUSB_ENDPOINT_OUT
        data = create_binary_buffer(data)
        return self._bulkTransfer(endpoint, data, sizeof(data), timeout)

    def bulkRead(self, endpoint, length, timeout=0):
        """
        Synchronous bulk read.
        timeout: in milliseconds, how long to wait for data. Set to 0 to
          disable.
        See bulkWrite for other parameters description.

        Returns received data.
        """
        endpoint = (endpoint & ~libusb1.USB_ENDPOINT_DIR_MASK) | \
                    libusb1.LIBUSB_ENDPOINT_IN
        data = create_binary_buffer(length)
        transferred = self._bulkTransfer(endpoint, data, length, timeout)
        return data.raw[:transferred]

    def _interruptTransfer(self, endpoint, data, length, timeout):
        transferred = c_int()
        result = libusb1.libusb_interrupt_transfer(self.__handle, endpoint,
            data, length, byref(transferred), timeout)
        if result:
            raise libusb1.USBError(result)
        return transferred.value

    def interruptWrite(self, endpoint, data, timeout=0):
        """
        Synchronous interrupt write.
        endpoint: endpoint to send data to.
        data: data to send.
        timeout: in milliseconds, how long to wait for device acknowledgement.
          Set to 0 to disable.

        Returns the number of bytes actually sent.
        """
        endpoint = (endpoint & ~libusb1.USB_ENDPOINT_DIR_MASK) | \
                    libusb1.LIBUSB_ENDPOINT_OUT
        data = create_binary_buffer(data)
        return self._interruptTransfer(endpoint, data, sizeof(data), timeout)

    def interruptRead(self, endpoint, length, timeout=0):
        """
        Synchronous interrupt write.
        timeout: in milliseconds, how long to wait for data. Set to 0 to
          disable.
        See interruptRead for other parameters description.

        Returns received data.
        """
        endpoint = (endpoint & ~libusb1.USB_ENDPOINT_DIR_MASK) | \
                    libusb1.LIBUSB_ENDPOINT_IN
        data = create_binary_buffer(length)
        transferred = self._interruptTransfer(endpoint, data, length, timeout)
        return data.raw[:transferred]

    def getTransfer(self, iso_packets=0):
        """
        Get an empty transfer for asynchronous use.
        iso_packets: the number of isochronous transfer descriptors to
          allocate.
        """
        return USBTransfer(self.__handle, iso_packets)

class USBDevice(object):
    """
    Represents a USB device.
    """

    __configuration_descriptor_list = None
    __libusb_unref_device = libusb1.libusb_unref_device
    __libusb_free_config_descriptor = libusb1.libusb_free_config_descriptor
    __byref = byref

    def __init__(self, context, device_p):
        """
        You should not instanciate this class directly.
        Call LibUSBContext methods to receive instances of this class.
        """
        # Important: device_p refcount must be incremented before being given
        # to this constructor. This class will decrement refcount upon
        # destruction.
        self.__context = context
        self.device_p = device_p
        # Fetch device descriptor
        device_descriptor = libusb1.libusb_device_descriptor()
        result = libusb1.libusb_get_device_descriptor(device_p,
            byref(device_descriptor))
        if result:
            raise libusb1.USBError(result)
        self.device_descriptor = device_descriptor
        # Fetch all configuration descriptors
        self.__configuration_descriptor_list = []
        append = self.__configuration_descriptor_list.append
        for configuration_id in xrange(device_descriptor.bNumConfigurations):
            config = libusb1.libusb_config_descriptor_p()
            result = libusb1.libusb_get_config_descriptor(device_p,
                configuration_id, byref(config))
            if result == libusb1.LIBUSB_ERROR_NOT_FOUND:
                # Some devices (ex windows' root hubs) tell they have one
                # configuration, but they have no configuration descriptor.
                continue
            if result:
                raise libusb1.USBError(result)
            append(config.contents)

    def __del__(self):
        self.__libusb_unref_device(self.device_p)
        if self.__configuration_descriptor_list is not None:
            byref = self.__byref
            for config in self.__configuration_descriptor_list:
                self.__libusb_free_config_descriptor(byref(config))

    def __str__(self):
        return 'Bus %03i Device %03i: ID %04x:%04x %s %s' % (
            self.getBusNumber(),
            self.getDeviceAddress(),
            self.getVendorID(),
            self.getProductID(),
            self.getManufacturer(),
            self.getProduct()
        )

    def reprConfigurations(self):
        """
        Get a string representation of device's configurations.
        Note: opens the device temporarily.
        """
        out = StringIO()
        for config in self.__configuration_descriptor_list:
            print >> out, 'Configuration %i: %s' % (config.bConfigurationValue,
                self._getASCIIStringDescriptor(config.iConfiguration))
            print >> out, '  Max Power: %i mA' % (config.MaxPower * 2, )
            # TODO: bmAttributes dump
            for interface_num in xrange(config.bNumInterfaces):
                interface = config.interface[interface_num]
                print >> out, '  Interface %i' % (interface_num, )
                for alt_setting_num in xrange(interface.num_altsetting):
                    altsetting = interface.altsetting[alt_setting_num]
                    print >> out, '    Alt Setting %i: %s' % (alt_setting_num,
                        self._getASCIIStringDescriptor(altsetting.iInterface))
                    print >> out, '      Class: %02x Subclass: %02x' % \
                        (altsetting.bInterfaceClass,
                         altsetting.bInterfaceSubClass)
                    print >> out, '      Protocol: %02x' % \
                        (altsetting.bInterfaceProtocol, )
                    for endpoint_num in xrange(altsetting.bNumEndpoints):
                        endpoint = altsetting.endpoint[endpoint_num]
                        print >> out, '      Endpoint %i' % (endpoint_num, )
                        print >> out, '        Address: %02x' % \
                            (endpoint.bEndpointAddress, )
                        attribute_list = []
                        transfer_type = endpoint.bmAttributes & \
                            libusb1.LIBUSB_TRANSFER_TYPE_MASK
                        attribute_list.append(libusb1.libusb_transfer_type(
                            transfer_type
                        ))
                        if transfer_type == \
                            libusb1.LIBUSB_TRANSFER_TYPE_ISOCHRONOUS:
                            attribute_list.append(libusb1.libusb_iso_sync_type(
                                (endpoint.bmAttributes & \
                                 libusb1.LIBUSB_ISO_SYNC_TYPE_MASK) >> 2
                            ))
                            attribute_list.append(libusb1.libusb_iso_usage_type(
                                (endpoint.bmAttributes & \
                                 libusb1.LIBUSB_ISO_USAGE_TYPE_MASK) >> 4
                            ))
                        print >> out, '        Attributes: %s' % \
                            (', '.join(attribute_list), )
                        print >> out, '        Max Packet Size: %i' % \
                            (endpoint.wMaxPacketSize, )
                        print >> out, '        Interval: %i' % \
                            (endpoint.bInterval, )
                        print >> out, '        Refresh: %i' % \
                            (endpoint.bRefresh, )
                        print >> out, '        Sync Address: %02x' % \
                            (endpoint.bSynchAddress, )
        return out.getvalue()

    def getBusNumber(self):
        """
        Get device's bus number.
        """
        return libusb1.libusb_get_bus_number(self.device_p)

    def getDeviceAddress(self):
        """
        Get device's address on its bus.
        """
        return libusb1.libusb_get_device_address(self.device_p)

    def getbcdUSB(self):
        """
        Get the USB spec version device complies to, in BCD format.
        """
        return self.device_descriptor.bcdUSB

    def getDeviceClass(self):
        """
        Get device's class id.
        """
        return self.device_descriptor.bDeviceClass

    def getDeviceSubClass(self):
        """
        Get device's subclass id.
        """
        return self.device_descriptor.bDeviceSubClass

    def getDeviceProtocol(self):
        """
        Get device's protocol id.
        """
        return self.device_descriptor.bDeviceProtocol

    def getMaxPacketSize0(self):
        """
        Get device's max packet size for endpoint 0 (control).
        """
        return self.device_descriptor.bMaxPacketSize0

    def getVendorID(self):
        """
        Get device's vendor id.
        """
        return self.device_descriptor.idVendor

    def getProductID(self):
        """
        Get device's product id.
        """
        return self.device_descriptor.idProduct

    def getbcdDevice(self):
        """
        Get device's release number.
        """
        return self.device_descriptor.bcdDevice

    def getSupportedLanguageList(self):
        """
        Get the list of language ids device has string descriptors for.
        """
        temp_handle = self.open()
        return temp_handle.getSupportedLanguageList()

    def _getStringDescriptor(self, descriptor, lang_id):
        if descriptor == 0:
            result = None
        else:
            temp_handle = self.open()
            result = temp_handle.getStringDescriptor(descriptor, lang_id)
        return result

    def _getASCIIStringDescriptor(self, descriptor):
        if descriptor == 0:
            result = None
        else:
            temp_handle = self.open()
            result = temp_handle.getASCIIStringDescriptor(descriptor)
        return result

    def getManufacturer(self):
        """
        Get device's manufaturer name.
        Note: opens the device temporarily.
        """
        return self._getASCIIStringDescriptor(
            self.device_descriptor.iManufacturer)

    def getProduct(self):
        """
        Get device's product name.
        Note: opens the device temporarily.
        """
        return self._getASCIIStringDescriptor(self.device_descriptor.iProduct)

    def getSerialNumber(self):
        """
        Get device's serial number.
        Note: opens the device temporarily.
        """
        return self._getASCIIStringDescriptor(
            self.device_descriptor.iSerialNumber)

    def getNumConfigurations(self):
        """
        Get device's number of possible configurations.
        """
        return self.device_descriptor.bNumConfigurations

    def open(self):
        """
        Open device.
        Returns an USBDeviceHandle instance.
        """
        handle = libusb1.libusb_device_handle_p()
        result = libusb1.libusb_open(self.device_p, byref(handle))
        if result:
            raise libusb1.USBError(result)
        return USBDeviceHandle(self.__context, handle)

class LibUSBContext(object):
    """
    libusb1 USB context.

    Provides methods to enumerate & look up USB devices.
    Also provides access to global (device-independent) libusb1 functions.
    """
    __libusb_exit = libusb1.libusb_exit
    __context_p = None
    __added_cb = None
    __removed_cb = None

    def __init__(self):
        """
        Create a new USB context.
        """
        context_p = libusb1.libusb_context_p()
        result = libusb1.libusb_init(byref(context_p))
        if result:
            raise libusb1.USBError(result)
        self.__context_p = context_p

    def __del__(self):
        self.exit()

    def exit(self):
        """
        Close (destroy) this USB context.
        """
        context_p = self.__context_p
        if context_p is not None:
            self.__libusb_exit(context_p)
            self.__context_p = None
        self.__added_cb = None
        self.__removed_cb = None

    def getDeviceList(self):
        """
        Return a list of all USB devices currently plugged in, as USBDevice
        instances.
        """
        device_p_p = libusb1.libusb_device_p_p()
        libusb_device_p = libusb1.libusb_device_p
        device_list_len = libusb1.libusb_get_device_list(self.__context_p,
                                                         byref(device_p_p))
        # Instanciate our own libusb_device_p object so we can free
        # libusb-provided device list. Is this a bug in ctypes that it doesn't
        # copy pointer value (=pointed memory address) ? At least, it's not so
        # convenient and forces using such weird code.
        result = [USBDevice(self, libusb_device_p(x.contents))
            for x in device_p_p[:device_list_len]]
        libusb1.libusb_free_device_list(device_p_p, 0)
        return result

    def openByVendorIDAndProductID(self, vendor_id, product_id):
        """
        Get the first USB device matching given vendor and product ids.
        Returns an USBDeviceHandle instance, or None if no present device
        match.
        """
        handle_p = libusb1.libusb_open_device_with_vid_pid(self.__context_p,
            vendor_id, product_id)
        if handle_p:
            result = USBDeviceHandle(self, handle_p)
        else:
            result = None
        return result

    def getPollFDList(self):
        """
        Return file descriptors to be used to poll USB events.
        You should not have to call this method, unless you are integrating
        this class with a polling mechanism.
        """
        pollfd_p_p = libusb1.libusb_get_pollfds(self.__context_p)
        if not pollfd_p_p:
            errno = get_errno()
            if errno:
                raise OSError(errno)
            else:
                # Assume not implemented
                raise NotImplementedError("Your libusb doesn't seem to "
                    "implement pollable FDs")
        try:
            result = []
            append = result.append
            fd_index = 0
            while pollfd_p_p[fd_index]:
                append((pollfd_p_p[fd_index].contents.fd,
                        pollfd_p_p[fd_index].contents.events))
                fd_index += 1
        finally:
            _free(pollfd_p_p)
        return result

    def handleEvents(self):
        """
        Handle any pending event (blocking).
        See libusb1 documentation for details (there is a timeout, so it's
        not "really" blocking).
        """
        result = libusb1.libusb_handle_events(self.__context_p)
        if result:
            raise libusb1.USBError(result)

    def handleEventsTimeout(self, tv=0):
        """
        Handle any pending event.
        If tv is 0, will return immediately after handling already-pending
        events.
        Othewire, defines the maximum amount of time to wait for events, in
        seconds.
        """
        if tv is None:
            tv = 0
        tv_s = int(tv)
        tv = libusb1.timeval(tv_s, int((tv - tv_s) * 1000000))
        result = libusb1.libusb_handle_events_timeout(self.__context_p,
            byref(tv))
        if result:
            raise libusb1.USBError(result)

    def setPollFDNotifiers(self, added_cb=None, removed_cb=None,
            user_data=None):
        """
        Give libusb1 methods to call when it should add/remove file descriptor
        for polling.
        You should not have to call this method, unless you are integrating
        this class with a polling mechanism.
        """
        if added_cb is None:
            added_cb = POINTER(None)
        else:
            added_cb = libusb1.libusb_pollfd_added_cb_p(added_cb)
        if removed_cb is None:
            removed_cb = POINTER(None)
        else:
            removed_cb = libusb1.libusb_pollfd_removed_cb_p(removed_cb)
        self.__added_cb = added_cb
        self.__removed_cb = removed_cb
        libusb1.libusb_set_pollfd_notifiers(self.__context_p, added_cb,
                                            removed_cb, user_data)

    def getNextTimeout(self):
        """
        Returns the next internal timeout that libusb needs to handle, in
        seconds, or None if no timeout is needed.
        You should not have to call this method, unless you are integrating
        this class with a polling mechanism.
        """
        timeval = libusb1.timeval()
        result = libusb1.libusb_get_next_timeout(self.__context_p,
            byref(timeval))
        if result == 0:
            result = None
        elif result == 1:
            result = timeval.tv_sec + (timeval.tv_usec * 0.000001)
        else:
            raise libusb1.USBError(result)
        return result

    def setDebug(self, level):
        """
        Set debugging level.
        Note: depending on libusb compilation settings, this might have no
        effect.
        """
        libusb1.libusb_set_debug(self.__context_p, level)

