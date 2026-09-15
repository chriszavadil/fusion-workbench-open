"""Read reference archive arrays without running notebook code. MIT."""
from pathlib import Path
import hashlib,json
import h5py,numpy as np
HERE=Path(__file__).resolve().parent
out={}
for kind,name in [('experiment','ofb_experiment.h5'),('computed_reference','ofb_openmc_endfb80.h5')]:
 p=HERE/'upstream'/name;rows={}
 with h5py.File(p) as h:
  for spectrum in ['nspectrum','gspectrum']:
   values=h[spectrum+'/table'][()]
   rows[spectrum]={n:values[n].tolist() for n in values.dtype.names}
 out[kind]={'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'spectra':rows}
(HERE/'ARCHIVE_PROJECTION.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('Exported two archives with all bins and uncertainty columns')
