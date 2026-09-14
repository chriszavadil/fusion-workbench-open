"""Windows-only runtime portability shim: close temp handles before unlink.
The upstream function unlinks open files, which Windows rejects. This changes
only temp-file cleanup order, not model equations, constraints or tolerances.
"""
import os
from pathlib import Path
from process.core.process_output import OutputFileManager

def install():
    if os.name!='nt':return
    def close_idempotence_files(cls,output_prefix):
        paths=[Path(cls._outfile.name),Path(cls._mfile.name)]
        expected=[Path(output_prefix+'IDEM_OUT.DAT'),Path(output_prefix+'IDEM_MFILE.DAT')]
        if paths!=expected:raise RuntimeError('Refuse to delete unexpected output files')
        cls._outfile.close();cls._mfile.close()
        for path in paths:path.unlink()
        cls.open_files(mode='a',output_prefix=output_prefix)
    OutputFileManager.close_idempotence_files=classmethod(close_idempotence_files)
