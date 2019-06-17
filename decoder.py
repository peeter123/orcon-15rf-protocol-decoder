import sys
import numpy as np
from bitstring import BitArray as ba

PREAMBLE = 0x55
STOP = 0x35
SYNC = [0xFF, 0x00, 0x33, 0x55, 0x53]
RAW_BYTE_LENGTH = 10
MANCH_ENC = [0xAA, 0xA9, 0xA6, 0xA5, 0x9A, 0x99, 0x96, 0x95,
             0x6A, 0x69, 0x66, 0x65, 0x5A, 0x59, 0x56, 0x55]
HEADER_FLAGS = [0x0F, 0x0C, 0x0D, 0x0B, 0x27, 0x24, 0x25, 0x23,
                0x47, 0x44, 0x45, 0x43, 0x17, 0x14, 0x15, 0x13]

class PacketException(Exception):
    """Base class for other exceptions"""
    pass


class PreambleError(PacketException):
    """Raised when the preamble is not valid"""
    pass


class SyncError(PacketException):
    """Raised when the sync byes are not valid"""
    pass


class EndOfPacketError(PacketException):
    """Raised when the preamble is not valid"""
    pass


class ManchesterDecodeError(PacketException):
    """Raised when the preamble is not valid"""
    pass


class ChecksumError(PacketException):
    """Raised when the preamble is not valid"""
    pass


class RF15Decoder:
    raw_message = ''
    decoded_message = []
    header = 0
    flags = 0
    type = ''
    addr0 = 0
    addr1 = 0
    addr2 = 0
    param0 = 0
    param1 = 0
    cmd = 0
    pkt_length = 0
    payload = []

    def __init__(self):
        pass

    def _pairwise(self, it):
        it = iter(it)
        while True:
            yield next(it), next(it)

    def _printf(self, format, *args):
        sys.stdout.write(format % args)
        sys.stdout.flush()

    def _is_information(self, flags):
        return flags & 0x20

    def _is_request(self, flags):
        return flags & 0x08

    def _is_response(self, flags):
        return flags & 0x10

    def _is_write(self, flags):
        return flags & 0x40

    def _has_addr0(self, flags):
        return flags & 0x01

    def _has_addr1(self, flags):
        return flags & 0x02

    def _has_addr2(self, flags):
        return flags & 0x04

    def _has_param0(self, header):
        return header & 0x02

    def _has_param1(self, header):
        return header & 0x01

    def prepare_message(self, rawmessage) -> list:
        """
        Parse the raw bitstring to decoded raw bytes with start stop bits removed and endianness fixed
        :param rawmessage:
        :return: list of bytes
        """

        if type(rawmessage) == ba:
            packet = rawmessage
        else:
            packet = ba(bin=rawmessage)

        try:
            # Sync on preamble
            counter = 0
            bit = packet[0]
            while packet[counter] == bit:
                bit = not bit
                counter += 1

            packet = packet << (counter - 2)

            # Split bin string to raw packets
            message = [packet[i:i + RAW_BYTE_LENGTH] for i in range(0, len(packet), RAW_BYTE_LENGTH)]

            # Remove start and stop bytes
            message = [byte[1:9] for byte in message]

            # Reverse bit order (Endianess is LSB)
            message = [byte[::-1] for byte in message]

            self.raw_message = ''.join(x.bin for x in message)

            return message
        except Exception:
            raise PreambleError()

    def extract_message(self, prepared_message: list) -> list:
        """
        Remove preamble, syncwords and end word
        :param prepared_message:
        :return:
        """

        # Remove sync words
        for i, x in enumerate(SYNC):
            if prepared_message[i].uint != x:
                raise SyncError()

        prepared_message = prepared_message[len(SYNC):len(prepared_message)]

        # Remove stop and rest of bogus data in packet
        index = prepared_message.index(ba(int=STOP, length=8))
        prepared_message = prepared_message[:index]

        # Convert to numpy uint8 datatype
        prepared_message = [np.uint8(x.uint) for x in prepared_message]

        return prepared_message

    def man_decode_message(self, extracted_message: list) -> list:
        """
        Manchester decode message
        :param extracted_message:
        :return:
        """

        decoded = []
        try:
            for a, b in self._pairwise(extracted_message):
                decoded.append((MANCH_ENC.index(a) << 4) + MANCH_ENC.index(b))
        except ValueError:
            raise ManchesterDecodeError()

        self.decoded_message = decoded

        return decoded

    def parse_message(self, decoded_message: list):
        # Verify checksum (sum of all data bytes + checksum byte should be 0)
        checksum = 0
        for x in decoded_message:
            checksum = (checksum + x) & 0xFF

        if checksum != 0:
            raise ChecksumError()

        # Parse Header
        self.header = decoded_message[0]
        self.flags = HEADER_FLAGS[(self.header >> 2) & 0x0F]
        del decoded_message[0]

        if self._is_information(self.flags):
            self._printf("--- INF --- ")
            self.type = 'INF'

        if self._is_request(self.flags):
            self._printf("--- REQ --- ")
            self.type = 'REQ'

        if self._is_response(self.flags):
            self._printf("--- RSP --- ")
            self.type = 'RSP'

        if self._is_write(self.flags):
            self._printf("--- WRT --- ")
            self.type = 'WRT'

        # Parse optional fields
        if self._has_addr0(self.flags):
            self.addr0 = (decoded_message[0] << 16) | (decoded_message[0] << 8) | decoded_message[0]
            self._printf('%02hu:%06lu ', np.uint8(self.addr0 >> 18) & 0x3F, self.addr0 & 0x3FFFF)
            decoded_message = decoded_message[3:]
        else:
            self._printf('--:------ ')

        if self._has_addr1(self.flags):
            self.addr1 = (decoded_message[0] << 16) | (decoded_message[0] << 8) | decoded_message[0]
            self._printf('%02hu:%06lu ', np.uint8(self.addr1 >> 18) & 0x3F, self.addr1 & 0x3FFFF)
            decoded_message = decoded_message[3:]
        else:
            self._printf('--:------ ')

        if self._has_addr2(self.flags):
            self.addr2 = (decoded_message[0] << 16) | (decoded_message[0] << 8) | decoded_message[0]
            self._printf('%02hu:%06lu ', np.uint8(self.addr2 >> 18) & 0x3F, self.addr2 & 0x3FFFF)
            decoded_message = decoded_message[3:]
        else:
            self._printf('--:------ ')

        if self._has_param0(self.header):
            param0 = decoded_message[0]
            self._printf('%03hu ', param0)
            decoded_message = decoded_message[1:]
        else:
            self._printf('--- ')

        if self._has_param1(self.header):
            param1 = decoded_message[0]
            self._printf('%03hu ', param1)
            decoded_message = decoded_message[1:]
        else:
            self._printf('--- ')

        # Parse Command
        self.cmd = (decoded_message[0] << 8) | decoded_message[0]
        self._printf('0x%04X ', self.cmd)
        decoded_message = decoded_message[2:]

        # Parse Length
        self.pkt_length = decoded_message[0]
        self._printf('%03hu ', self.pkt_length)
        decoded_message = decoded_message[1:]

        # Get Payload
        self.payload = decoded_message[0:self.pkt_length]
        for x in self.payload:
            self._printf('%02hX', x)

        # End of packet
        self._printf('\n')

    def decode(self, message):
        message = self.prepare_message(message)
        message = self.extract_message(message)
        message = self.man_decode_message(message)
        self.parse_message(message)
