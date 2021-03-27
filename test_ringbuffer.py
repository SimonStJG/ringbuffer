from collections import namedtuple

import pytest
import ringbuffer

SAMPLE_ELEMENTS = [f"{i:04}".encode("ascii") for i in range(0, 9999)]


@pytest.fixture(params=[0, 1, 9, 15])
def rb(request):
    with ringbuffer.RingBuffer(10, 4) as under_test:
        # Rotate the ring buffer position by various amounts, so we test behaviour when the buffer rolls around
        for i in range(0, request.param):
            assert under_test.try_write(b"0000")
            assert under_test.try_read() == b"0000"
        yield under_test


def test_read_write(rb):
    element = SAMPLE_ELEMENTS[0]
    assert rb.try_write(element)
    assert rb.try_read() == element


def test_read_write_multiple(rb):
    assert rb.try_write(SAMPLE_ELEMENTS[0])
    assert rb.try_write(SAMPLE_ELEMENTS[1])
    assert rb.try_read() == SAMPLE_ELEMENTS[0]
    assert rb.try_write(SAMPLE_ELEMENTS[2])
    assert rb.try_write(SAMPLE_ELEMENTS[3])
    assert rb.try_read() == SAMPLE_ELEMENTS[1]
    assert rb.try_read() == SAMPLE_ELEMENTS[2]
    assert rb.try_read() == SAMPLE_ELEMENTS[3]


def test_wraparound(rb):
    for element in SAMPLE_ELEMENTS:
        assert rb.try_write(element)
        assert rb.try_read() == element


def test_write_max(rb):
    elements = SAMPLE_ELEMENTS[:10]
    for element in elements:
        assert rb.try_write(element)
    for element in elements:
        assert rb.try_read() == element


def test_cant_write_if_full(rb):
    elements = SAMPLE_ELEMENTS[:10]
    for element in elements:
        assert rb.try_write(element)

    assert not rb.try_write("bXXXX")
    for element in elements:
        assert rb.try_read() == element


def test_read_empty(rb):
    assert rb.try_read() is None


def test_is_full(rb):
    elements = SAMPLE_ELEMENTS[:10]
    for element in elements:
        assert not rb.is_full()
        assert rb.try_write(element)

    assert rb.is_full()


def test_is_empty(rb):
    elements = SAMPLE_ELEMENTS[:10]

    assert rb.is_empty()
    for element in elements:
        assert rb.try_write(element)
        assert not rb.is_empty()


def test_size(rb):
    elements = SAMPLE_ELEMENTS[:10]

    for idx, element in enumerate(elements):
        assert rb.size() == idx
        assert rb.try_write(element)


def test_struct_marshalling_ringbuffer():
    datatype = namedtuple("datatype", field_names=["val0", "val1", "val2"])

    with ringbuffer.StructMarshallingRingBuffer(10, "iii") as under_test:
        assert under_test.try_write(datatype(1, 2, 3))
        assert under_test.try_write(datatype(4, 5, 6))
        assert under_test.try_write(datatype(7, 8, 9))

        assert under_test.try_read() == (1, 2, 3)
        assert under_test.try_read() == (4, 5, 6)
        assert under_test.try_read() == (7, 8, 9)
