"""Disposable PDF parser: no network, bounded CPU/address space/output and wall time."""
import json
import sys

def limits():
    if sys.platform != 'win32':
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024,256*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU, (5,5))
    else:
        # Per-process job limit on Windows; never change machine-wide policy.
        import ctypes as c
        from ctypes import wintypes as w
        class Basic(c.Structure):
            _fields_=[('process',c.c_longlong),('job',c.c_longlong),('flags',w.DWORD),('min',c.c_size_t),('max',c.c_size_t),('active',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
        class IO(c.Structure):
            _fields_=[(n,c.c_ulonglong) for n in ('readops','writeops','otherops','readbytes','writebytes','otherbytes')]
        class Extended(c.Structure):
            _fields_=[('basic',Basic),('io',IO),('process_memory',c.c_size_t),('job_memory',c.c_size_t),('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
        kernel=c.WinDLL('kernel32',use_last_error=True)
        kernel.CreateJobObjectW.restype=w.HANDLE
        kernel.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD]
        kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
        kernel.GetCurrentProcess.restype=w.HANDLE
        job=kernel.CreateJobObjectW(None,None)
        info=Extended();info.basic.flags=0x100|0x2;info.basic.process=5*10_000_000;info.process_memory=256*1024*1024
        if not job or not kernel.SetInformationJobObject(job,9,c.byref(info),c.sizeof(info)) or not kernel.AssignProcessToJobObject(job,kernel.GetCurrentProcess()):
            raise RuntimeError('PDF resource isolation unavailable')

def main():
    try:
        limits()
        import io
        from pypdf import PdfReader
        doc=PdfReader(io.BytesIO(sys.stdin.buffer.read(2*1024*1024+1)))
        if doc.is_encrypted: raise ValueError('encrypted')
        if len(doc.pages)>100: raise ValueError('page_limit')
        pages=[];total=0
        for i,page in enumerate(doc.pages):
            contents=page.get_contents()
            if contents and len(contents.get_data())>8*1024*1024:raise ValueError('stream_limit')
            text=page.extract_text() or '';total+=len(text)
            if total>250000:raise ValueError('text_limit')
            pages.append(dict(page=i+1,text=text))
        if not any(p['text'].strip() for p in pages):raise ValueError('no extractable text')
        print(json.dumps({'pages':pages},ensure_ascii=True))
    except Exception as exc:
        reason=str(exc) if isinstance(exc,ValueError) and str(exc) in ('encrypted','page_limit','stream_limit','text_limit','no extractable text') else 'parse_or_resource_limit'
        print(json.dumps({'error':reason}))
if __name__=='__main__':main()
