import ctypes
import mmap
import struct
from multiprocessing import sharedctypes


class RingBuffer:
    """
    Single producer single consumer lock free ringbuffer backed by an anonymous memory mapped file.

    Thread-safe only if there is a single consumer and a single producer.
    """

    def __init__(self, slots, obj_size):
        self._slots = slots
        self._obj_size = obj_size
        self._mm = None
        self._head = sharedctypes.RawValue(ctypes.c_uint, 0)
        self._tail = sharedctypes.RawValue(ctypes.c_uint, 0)

    def __enter__(self):
        self._mm = mmap.mmap(-1, (self._slots + 1) * self._obj_size)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._mm.close()

    def try_write(self, element):
        if self.is_full():
            return False
        self._marshall(element)
        self._head.value = (self._head.value + 1) % (self._slots + 1)
        return True

    def try_read(self):
        if self.is_empty():
            return None
        ret = self._unmarshall()
        self._tail.value = (self._tail.value + 1) % (self._slots + 1)
        return ret

    def is_empty(self):
        return self._head.value == self._tail.value

    def is_full(self):
        return (self._head.value + 1) % (self._slots + 1) == self._tail.value

    def size(self):
        if self._head.value >= self._tail.value:
            return self._head.value - self._tail.value
        return self._head.value + self._slots - self._tail.value + 1

    def _marshall(self, element):
        self._mm.seek(self._head.value * self._obj_size)
        self._mm.write(element)

    def _unmarshall(self):
        return self._mm[
            self._tail.value * self._obj_size : (self._tail.value + 1) * self._obj_size
        ]


class StructMarshallingRingBuffer(RingBuffer):
    def __init__(self, slots, fmt):
        self._fmt = fmt
        super().__init__(slots, obj_size=struct.calcsize(fmt))

    def _marshall(self, element):
        struct.pack_into(
            self._fmt, self._mm, self._head.value * self._obj_size, *element
        )

    def _unmarshall(self):
        return struct.unpack_from(
            self._fmt, self._mm, self._tail.value * self._obj_size
        )
