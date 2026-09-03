import numpy as np, pandas as pd, scipy.io as sio
base = '/mnt/data/'
files = ['sub-36_eeg_corrected.npz','sub-37_eeg_corrected.npz','sub-38_eeg_corrected.npz',
         'sub-39_eeg_corrected.npz','sub-40_eeg_corrected.npz']
arrs = {f: np.load(base+f, allow_pickle=True) for f in files}

for f in files:
    d = arrs[f]
    print(f, 'data max|.|=', np.abs(d['data']).max(),
          'epochs max|.|=', np.abs(d['epochs']).max())

r = files[0]
for f in files[1:]:
    print(f, 'identical data to sub-36:',
          np.array_equal(arrs[r]['data'], arrs[f]['data']),
          'identical epochs:', np.array_equal(arrs[r]['epochs'], arrs[f]['epochs']))

print('ch_names:', list(arrs[r]['ch_names']))
print('conditions:', list(arrs[r]['conditions']),
      'onsets:', arrs[r]['onsets'], 'group:', arrs[r]['group'])
t = arrs[r]['times']
print('times', t[0], '->', t[-1], 'dt=', t[1]-t[0])

for c in ['erp_data_clean.csv','eeg_real_waveforms.csv','eeg_psd_summary.csv','eeg_real_waveforms-(2).csv']:
    df = pd.read_csv(base+c)
    print('--', c, df.shape, list(df.columns)[:8])

for m in ['hai_indices_data.mat','spectral_power_data.mat','erp_raw_data.mat']:
    md = sio.loadmat(base+m)
    print('--', m, 'keys:', [k for k in md if not k.startswith('__')])
