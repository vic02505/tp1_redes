class Datagram:
    def __init__(self, num, total, size, data):
        self.num = num
        self.total = total
        self.size = size
        self.data = data

    @classmethod
    def builder(cls):
        return cls.DatagramBuilder()

    class DatagramBuilder:
        def __init__(self):
            self._num = 0
            self._total = 0
            self._size = 0
            self._data = bytearray(4000)

        def num(self, num):
            self._num = num
            return self

        def total(self, total):
            self._total = total
            return self

        def size(self, size):
            self._size = size
            return self

        def data(self, data):
            if len(data) != 4000:
                raise ValueError("Data must be a bytearray of 4000 bytes")
            self._data = data
            return self

        def build(self):
            return Datagram(self._num, self._total, self._size, self._data)
        
class Header:
    def __init__(self, file_name, file_size, packet_count):
        self.file_name = file_name
        self.file_size = file_size
        self.packet_count = packet_count

    @classmethod
    def builder(cls):
        return cls.HeaderBuilder()

    class HeaderBuilder:
        def __init__(self):
            self._file_name = ""
            self._file_size = 0
            self._packet_count = 0

        def file_name(self, file_name):
            self._file_name = file_name
            return self

        def file_size(self, file_size):
            self._file_size = file_size
            return self

        def packet_count(self, packet_count):
            self._packet_count = packet_count
            return self

        def build(self):
            return Header(self._file_name, self._file_size, self._packet_count)
        
class ACK:
    def __init__(self, id):
        self.id = id

    @classmethod
    def builder(cls):
        return cls.ACKBuilder()

    class ACKBuilder:
        def __init__(self):
            self._id = 0

        def id(self, id):
            self._id = id
            return self

        def build(self):
            return ACK(self._id)