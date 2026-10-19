"""Read a PowerShell DPAPI SecureString on the owning Windows account, in memory.

Avoid nested PowerShell module/command resolution. No plaintext is printed or
written. This helper is used by owner-side CLI tooling, never by model tools.
"""
import ctypes
import os
from pathlib import Path

def protect(value,path):
    path=Path(path).resolve()
    if os.name!='nt' or path.drive.lower()!='d:':raise RuntimeError('Owner credentials require a private D: destination.')
    data=value.encode('utf-16-le')
    class Blob(ctypes.Structure):_fields_=[('size',ctypes.c_uint32),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=(ctypes.c_ubyte*len(data)).from_buffer_copy(data);source=Blob(len(data),buffer);output=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    crypt.CryptProtectData.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(Blob)]
    crypt.CryptProtectData.restype=ctypes.c_int
    if not crypt.CryptProtectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(output)):raise RuntimeError('Windows DPAPI encryption failed.')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.LocalFree.argtypes=[ctypes.c_void_p]
    try:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(ctypes.string_at(output.data,output.size).hex(),encoding='utf-8')
    finally:
        ctypes.memset(output.data,0,output.size);kernel.LocalFree(ctypes.cast(output.data,ctypes.c_void_p))


def unprotect(path):
    path=Path(path).resolve()
    if os.name!='nt' or path.drive.lower()!='d:':
        raise RuntimeError('Owner credentials require the owning Windows account and a D: private path.')
    encrypted=bytes.fromhex(path.read_text(encoding='utf-8-sig').strip())
    class Blob(ctypes.Structure):
        _fields_=[('size',ctypes.c_uint32),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=(ctypes.c_ubyte*len(encrypted)).from_buffer_copy(encrypted)
    source=Blob(len(encrypted),buffer);output=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    crypt.CryptUnprotectData.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.restype=ctypes.c_int
    if not crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(output)):
        raise RuntimeError('Windows DPAPI could not decrypt this credential for the current account.')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p]
    try:
        return ctypes.string_at(output.data,output.size).decode('utf-16-le')
    finally:
        ctypes.memset(output.data,0,output.size)
        kernel.LocalFree(ctypes.cast(output.data,ctypes.c_void_p))
