

#!/usr/bin/python

import mmap
import struct
import sys
import ctypes

'''
TODO:  PAGESIZE is not used, but it should.  When mmap is used
the address must be on a page boundry, but the addresses used will be

'''
VERSION = '0.0.1'

USAGE = '''fwloader: load M4 firmware and start.
Usage:
    python fwloader.py [options] FILE [ FILE ... ]

Options:
    -h, --help              this help message.
    -v, --version           version info.
'''




"""
This is from imx-regs.h from u-boot
struct src {
	u32	    scr;
	u32	    sbmr1;
	u32	    srsr;
	u32	    reserved1[2];
	u32	    sisr;
	u32	    simr;
	u32     sbmr2;
	u32     gpr1;
	u32     gpr2;
	u32     gpr3;
	u32     gpr4;
	u32     gpr5;
	u32     gpr6;
	u32     gpr7;
	u32     gpr8;
	u32     gpr9;
	u32     gpr10;
};
"""

class src(ctypes.Structure):

    _fields_=[
        ("scr", ctypes.c_uint),
        ("sbmr1", ctypes.c_uint),
        ("srsr", ctypes.c_uint),
        ("reserved1" , ctypes.c_uint *2),
        ("sisr",ctypes.c_uint),
        ("simr",ctypes.c_uint),
        ("sbmr2",ctypes.c_uint),
        ("gpr1",ctypes.c_uint),
        ("gpr2",ctypes.c_uint),
        ("gpr3",ctypes.c_uint),
        ("gpr4",ctypes.c_uint),
        ("gpr5",ctypes.c_uint),
        ("gpr6",ctypes.c_uint),
        ("gpr7",ctypes.c_uint),
        ("gpr8",ctypes.c_uint),
        ("gpr9", ctypes.c_uint),
        ("gpr10", ctypes.c_uint),
    ]

SRC_BASE_ADDR = ((0x02000000 + 0x80000) + 0x58000)

'''
From the A9
    0080_0000 008F_FFFF is SRAM TCMU 32 * 1024 (32K)

    007F_8000 007F_FFFF is SRAM TCML 32 * 1024 (32K)

    TCML is alias to 0x0 -- 0x7FFF so, this is used for
    reset vector

'''
M4_BOOTROM_BASE_ADDR = 0x007F8000


def arch_auxiliary_core_check_up(core_id):

    print("Size of src: ", ctypes.sizeof(src))
    try:
        with open("/dev/mem", "r+b") as fd:

            mem =mmap.mmap(fd.fileno(),length =ctypes.sizeof(src),
                           flags=mmap.MAP_SHARED,
                           prot=mmap.PROT_WRITE | mmap.PROT_READ,
                           offset=SRC_BASE_ADDR)

            mapped_src = src.from_buffer(mem)

            if mapped_src.scr & 0x00000010:
                return 0
            return 1
    except Exception as ex:
        print("OK something happend ", str(ex))
        raise RuntimeError('could open or map memory')


def set_stack_pc(pc,stack):

    print("Size of src: ", ctypes.sizeof(src))
    try:
        with open("/dev/mem", "r+b") as fd:

            mem =mmap.mmap(fd.fileno(),length =ctypes.sizeof(src),
                           flags=mmap.MAP_SHARED, prot=mmap.PROT_WRITE | mmap.PROT_READ,offset=M4_BOOTROM_BASE_ADDR)

            print("set_stack_pc: write")
            mem[0:3] = struct.pack("<L", stack)
            mem[4:7] = struct.pack("<L", pc)

            print("set_stack_pc: close")

            mem.close()
            return 0

    except Exception as ex:
        print("OK something happend ", str(ex))
        raise RuntimeError('could open or map memory')


def reset_start_M4(start=False):

    print("Size of src: ", ctypes.sizeof(src))

    try:
        with open("/dev/mem", "r+b") as fd:

            mem =mmap.mmap(fd.fileno(),length =ctypes.sizeof(src),
                           flags=mmap.MAP_SHARED,
                           prot=mmap.PROT_WRITE | mmap.PROT_READ,
                           offset=SRC_BASE_ADDR)

            if start:
                #read, or, write
                mapped_src = src.from_buffer(mem)
                mapped_src.scr |= 0x00400000
                mem[0:3] = mapped_src.scr

                #read, mask, write
                mapped_src = src.from_buffer(mem)
                mapped_src.scr &= ~0x00000010
                mem[0:3] = mapped_src.scr

            else:
                #read, or, write
                mapped_src = src.from_buffer(mem)
                mapped_src.scr |= 0x00000010
                mem[0:3] = mapped_src.scr

            print("close mem")
            mem.close()

    except Exception as ex:
        print("OK something happend ", str(ex))
        raise RuntimeError('could open or map memory')

    return 0


'''

if pc and stack are 0, then don't load PC or stack
then the code is loaded at the reset vector; using intel hex
'''

def arch_auxiliary_core_up(core_id, pc=0, stack=0):

    print("Size of src: ", ctypes.sizeof(src))
    try:
        with open("/dev/mem", "r+b") as fd:

            mem =mmap.mmap(fd.fileno(),
                           length =ctypes.sizeof(src),
                           flags=mmap.MAP_SHARED,
                           prot=mmap.PROT_WRITE | mmap.PROT_READ,
                           offset=SRC_BASE_ADDR)

            mapped_src = src.from_buffer(mem)

            if mapped_src.scr & 0x00000010:
                return 0
            return 1
    except Exception as ex:
        print("OK something happend ", str(ex))
        raise RuntimeError('could open or map memory')



def loadM4MemoryWithCode(address, data, len):

    if  address % mmap.ALLOCATIONGRANULARITY:
        raise RuntimeError("Address is not align " +
                           str(address) +
                           " boundry " +
                           str(mmap.ALLOCATIONGRANULARITY))

    try:
        with open("/dev/mem", "r+b") as fd:

            mem =mmap.mmap(fd.fileno(),length =len,
                           flags=mmap.MAP_SHARED,
                           prot=mmap.PROT_WRITE | mmap.PROT_READ,
                           offset=address)

            print("mem write")
            mem[0:len]=data
            print("Close mem")
            mem.close()

            return 0
    except Exception as ex:
        print("OK something happend ", str(ex))
        raise RuntimeError('could open or map memory')




def main():

    print("Arguments passed ", len(sys.argv))

    try:
        if arch_auxiliary_core_check_up(0):
            print("M4 is running .. shutdown M4")


        else:
            print("Core is not running")
    except RuntimeError as ex:
        print("Error:", str(ex))


if __name__ == '__main__':
    sys.exit(main())
    


