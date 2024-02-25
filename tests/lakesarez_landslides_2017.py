# -*- coding: utf-8 -*-
"""LakeSarez_Landslides_2017.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1O3aZtZsTrQIldvCqlVRel13wJRLhmTJt

## PyGMTSAR SBAS and PSI Analyses: Lake Sarez Landslides, Tajikistan

This exploration reproduces the findings shared in the following paper: [Integration of satellite SAR and optical acquisitions for the characterization of the Lake Sarez landslides in Tajikistan](https://www.researchgate.net/publication/378176884_Integration_of_satellite_SAR_and_optical_acquisitions_for_the_characterization_of_the_Lake_Sarez_landslides_in_Tajikistan).

The PyGMTSAR InSAR library, Geomed3D Geophysical Inversion Library, N-Cube 3D/4D GIS Data Visualization, among others, are my open-source projects developed in my free time. I hold a Master's degree in STEM, specializing in radio physics. In 2004, I received the first prize in the All-Russian Physics Competition for significant results in forward and inverse modeling for nonlinear optics and holography. These skills are also applicable to modeling Gravity, Magnetic, and Thermal fields, as well as satellite interferometry processing. With 20 years of experience as a data scientist and software developer, I have contributed to scientific and industrial development, working on government contracts, university projects, and with companies like LG Corp and Google Inc.

You can support my work on [Patreon](https://www.patreon.com/pechnikov), where I share updates on my projects, publications, use cases, examples, and other useful information. For research and development services and support, please visit my profile on the freelance platform [Upwork](https://www.upwork.com).

### Resources
- Google Colab Pro notebooks and articles on [Patreon](https://www.patreon.com/pechnikov),
- Google Colab notebooks on [GitHub](https://github.com),
- Docker Images on [DockerHub](https://hub.docker.com),
- Geological Models on [YouTube](https://www.youtube.com),
- VR/AR Geological Models on [GitHub](https://github.com),
- Live updates and announcements on [LinkedIn](https://www.linkedin.com/in/alexey-pechnikov/).

© Alexey Pechnikov, 2024

$\large\color{blue}{\text{Hint: Use menu Cell} \to \text{Run All or Runtime} \to \text{Complete All or Runtime} \to \text{Run All}}$
$\large\color{blue}{\text{(depending of your localization settings) to execute the entire notebook}}$

## Load Modules to Check Environment
"""

import platform, sys, os

"""## Google Colab Installation

### Install GMTSAR
https://github.com/gmtsar/gmtsar
"""

if 'google.colab' in sys.modules:
    count = !ls /usr/local | grep GMTSAR | wc -l
    if count == ['0']:
        !export DEBIAN_FRONTEND=noninteractive
        !apt-get update > /dev/null
        !apt install -y csh autoconf gfortran \
            libtiff5-dev libhdf5-dev liblapack-dev libgmt-dev gmt-dcw gmt-gshhg gmt  > /dev/null
        # GMTSAR codes are not so good to be compiled by modern GCC
        !apt install gcc-9 > /dev/null
        !update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 10
        !update-alternatives --config gcc
        !gcc --version | head -n 1
        !rm -fr /usr/local/GMTSAR
        !git config --global advice.detachedHead false
        !cd /usr/local && git clone -q --branch master https://github.com/gmtsar/gmtsar GMTSAR
        # revert recent broken commit
        !cd /usr/local/GMTSAR && git checkout e98ebc0f4164939a4780b1534bac186924d7c998 > /dev/null
        !cd /usr/local/GMTSAR && autoconf > /dev/null
        !cd /usr/local/GMTSAR && ./configure --with-orbits-dir=/tmp > /dev/null
        !cd /usr/local/GMTSAR && make 1>/dev/null 2>/dev/null
        !cd /usr/local/GMTSAR && make install >/dev/null
        # fix for missed script, use bash instead of csh interpretator
        # note: csh messes stdout and stderr in Docker environment, it's resolved in PyGMTSAR code
        !echo '#!/bin/sh' > /usr/local/GMTSAR/bin/gmtsar_sharedir.csh
        !echo echo /usr/local/GMTSAR/share/gmtsar >> /usr/local/GMTSAR/bin/gmtsar_sharedir.csh
        !chmod a+x /usr/local/GMTSAR/bin/gmtsar_sharedir.csh
        !/usr/local/GMTSAR/bin/gmtsar_sharedir.csh
        # test one GMTSAR binary
        !/usr/local/GMTSAR/bin/make_s1a_tops 2>&1 | head -n 2

import sys
if 'google.colab' in sys.modules:
    !apt install -y xvfb > /dev/null
    !{sys.executable} -m pip install pyvista xvfbwrapper > /dev/null
    import xvfbwrapper
    display = xvfbwrapper.Xvfb(width=800, height=600)
    display.start()

"""### Define ENV Variables for Jupyter Instance"""

# Commented out IPython magic to ensure Python compatibility.
# use default GMTSAR installation path
PATH = os.environ['PATH']
if PATH.find('GMTSAR') == -1:
    PATH = os.environ['PATH'] + ':/usr/local/GMTSAR/bin/'
#     %env PATH {PATH}

"""### Install Python Modules

Maybe you need to restart your notebook, follow the instructions printing below.

The installation takes a long time on fresh Debian 10 and a short time on Google Colab
"""

!{sys.executable} --version

if 'google.colab' in sys.modules:
    !{sys.executable} -m pip install -Uq git+https://github.com/mobigroup/gmtsar.git@pygmtsar2#subdirectory=pygmtsar
    #!{sys.executable} -m pip install -q pygmtsar
from pygmtsar import __version__
__version__

"""## Load and Setup Python Modules"""

import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
import json
from dask.distributed import Client
import dask
import warnings
warnings.filterwarnings('ignore')

# Commented out IPython magic to ensure Python compatibility.
# plotting modules
import pyvista as pv
# magic trick for white background
pv.set_plot_theme("document")
import panel
panel.extension('vtk')
from contextlib import contextmanager
import matplotlib.pyplot as plt
@contextmanager
def mpl_settings(settings):
    original_settings = {k: plt.rcParams[k] for k in settings}
    plt.rcParams.update(settings)
    yield
    plt.rcParams.update(original_settings)
plt.rcParams['figure.figsize'] = [12, 4]
plt.rcParams['figure.dpi'] = 150
plt.rcParams['figure.titlesize'] = 24
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
# %matplotlib inline

# define Pandas display settings
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 100)

from pygmtsar import S1, Stack, tqdm_dask, NCubeVTK, ASF, AWS, ESA, GMT, XYZTiles, utils
if os.path.exists('/.dockerenv') and not 'google.colab' in sys.modules:
    # use different NetCDF backend in Docker containers
    from pygmtsar import datagrid
    datagrid.netcdf_engine = 'netcdf4'

"""## Define Sentinel-1 SLC Scenes and Processing Parameters

When you need more scenes and SBAS analysis  see examples on PyGMTSAR GitHub page https://github.com/mobigroup/gmtsar

### Descending Orbit Configuration

https://search.asf.alaska.edu/#/?polygon=POINT(72.66%2038.25)&start=2016-12-31T17:00:00Z&end=2017-12-31T16:59:59Z&productTypes=SLC&resultsLoaded=true&zoom=7.131&center=74.457,35.638&path=5-5&frame=466-466
"""

SCENES = """
S1A_IW_SLC__1SDV_20171225T011405_20171225T011433_019852_021C64_4328
S1A_IW_SLC__1SDV_20171213T011406_20171213T011434_019677_021703_7F07
S1A_IW_SLC__1SDV_20171201T011406_20171201T011434_019502_021186_9E02
S1A_IW_SLC__1SDV_20171119T011407_20171119T011435_019327_020C0E_0E4F
S1A_IW_SLC__1SDV_20171107T011407_20171107T011435_019152_020694_2D73
S1A_IW_SLC__1SDV_20171026T011407_20171026T011435_018977_020128_3CBC
S1A_IW_SLC__1SDV_20171014T011407_20171014T011435_018802_01FBD8_0578
S1A_IW_SLC__1SDV_20171002T011407_20171002T011434_018627_01F688_47CF
S1A_IW_SLC__1SDV_20170920T011407_20170920T011435_018452_01F124_C9FA
S1A_IW_SLC__1SDV_20170908T011406_20170908T011434_018277_01EBC2_3B58
S1A_IW_SLC__1SDV_20170827T011406_20170827T011434_018102_01E66B_DD3B
S1A_IW_SLC__1SDV_20170815T011405_20170815T011433_017927_01E120_4FCB
S1A_IW_SLC__1SDV_20170803T011405_20170803T011432_017752_01DBCB_D70F
S1A_IW_SLC__1SDV_20170722T011404_20170722T011432_017577_01D673_6CEC
S1A_IW_SLC__1SDV_20170710T011403_20170710T011431_017402_01D121_09CC
S1A_IW_SLC__1SDV_20170616T011402_20170616T011430_017052_01C689_6B1C
S1A_IW_SLC__1SDV_20170604T011401_20170604T011429_016877_01C124_6EF9
S1A_IW_SLC__1SDV_20170523T011400_20170523T011428_016702_01BBBA_C1C8
S1A_IW_SLC__1SDV_20170511T011400_20170511T011428_016527_01B650_1364
"""
SCENES = list(filter(None, SCENES.split('\n')))
print (f'Scenes defined: {len(SCENES)}')

ORBIT     = 'D'
SUBSWATH  = 2
REFERENCE = '2017-08-27'

WORKDIR = 'raw_sarez2017_' + 'desc'  if ORBIT == 'D' else 'asc'
DATADIR = 'data_sarez2017_' + 'desc' if ORBIT == 'D' else 'asc'

# define DEM filename inside data directory
DEM = f'{DATADIR}/dem.nc'

# subsidence point from
geojson = '''
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [72.66, 38.25]
  },
  "properties": {}
}
'''
POI = gpd.GeoDataFrame.from_features([json.loads(geojson)])
POI

geojson = '''
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [72.63, 38.26]
  },
  "properties": {}
}
'''
BUFFER = 0.09
AOI = gpd.GeoDataFrame.from_features([json.loads(geojson)])
AOI['geometry'] = AOI.buffer(BUFFER)
AOI

"""## Download and Unpack Datasets

## Enter Your ASF and ESA User and Password

If the data directory is empty or doesn't exist, you'll need to download Sentinel-1 scenes from the Alaska Satellite Facility (ASF) datastore. Use your Earthdata Login credentials. If you don't have an Earthdata Login, you can create one at https://urs.earthdata.nasa.gov//users/new Also, register your ESA Copernicus datastore account at https://dataspace.copernicus.eu/

You can also use pre-existing SLC scenes stored on your Google Drive, or you can copy them using a direct public link from iCloud Drive.

The credentials below are available at the time the notebook is validated.
"""

# Set these variables to None and you will be prompted to enter your username and password below.
asf_username = 'GoogleColab2023'
asf_password = 'GoogleColab_2023'

esa_username = 'sifts0_spangle@icloud.com'
esa_password = 'cnjwdchuwe&e9d0We9'

# Set these variables to None and you will be prompted to enter your username and password below.
asf = ASF(asf_username, asf_password)
# Optimized scene downloading from ASF - only the required subswaths and polarizations.
print(asf.download_scenes(DATADIR, SCENES, SUBSWATH))
# There are two ways to download orbits; you can use any one or both together.
try:
    # RESORB orbit downloading from ASF has recently failed.
    print(asf.download_orbits(DATADIR))
except Exception as e:
    print (e)
    # Download missed orbits in case ASF orbit downloading fails.
    esa = ESA(esa_username, esa_password)
    print (esa.download_orbits(DATADIR))

# previously, PyGMTSAR internally applied 0.1° buffer
try:
    # download SRTM DEM from GMT servers
    # note: downloading often fails recently
    GMT().download_dem(AOI, filename=DEM)
except Exception as e:
    print (e)

# if DEM missed, download Copernicus DEM from open AWS datastore
# get complete 1°x1° tiles covering the AOI, crop them later using AOI
AWS().download_dem(AOI, filename=DEM)
# don't worry about messages 'ERROR 3: /vsipythonfilelike/ ... : I/O error'

"""## Run Local Dask Cluster

Launch Dask cluster for local and distributed multicore computing. That's possible to process terabyte scale Sentinel-1 SLC datasets on Apple Air 16 GB RAM.
"""

# simple Dask initialization
if 'client' in globals():
    client.close()
client = Client()
client

"""## Init

Search recursively for measurement (.tiff) and annotation (.xml) and orbit (.EOF) files in the DATA directory. It can be directory with full unzipped scenes (.SAFE) subdirectories or just a directory with the list of pairs of required .tiff and .xml files (maybe pre-filtered for orbit, polarization and subswath to save disk space). If orbit files and DEM are missed these will be downloaded automatically below.

### Select Original Secenes and Orbits

Use filters to find required subswath, polarization and orbit in original scenes .SAFE directories in the data directory.
"""

scenes = S1.scan_slc(DATADIR, subswath=SUBSWATH)
# use only the specified scenes
scenes = scenes[scenes.index.str.replace('-','').isin([scene.split('_')[5][:8] for scene in SCENES])]

sbas = Stack(WORKDIR, drop_if_exists=True).set_scenes(scenes).set_reference(REFERENCE)
sbas.to_dataframe()

sbas.plot_scenes(AOI=AOI)

"""## Reframe Scenes (Optional)

Stitch sequential scenes and crop the subswath to a smaller area for faster processing when the full area is not needed.
"""

sbas.compute_reframe(AOI)

sbas.plot_scenes(AOI=AOI)

"""### Load DEM

The function below loads DEM from file or Xarray variable and converts heights to ellipsoidal model using EGM96 grid.
"""

# define the area of interest (AOI) to speedup the processing
sbas.load_dem(DEM, AOI)

sbas.plot_scenes(AOI=AOI)

"""## Align Images"""

if os.path.exists('/.dockerenv') and not 'google.colab' in sys.modules:
    # use special joblib backend in Docker containers
    sbas.compute_align(joblib_aligning_backend='threading')
else:
    sbas.compute_align()

"""## Backup"""

# bursts-cropped GeoTIFF files moved into backup directory
sbas.backup('backup')

# free disk space removing the cropped Sentinel-1 GeoTIFFs
# alternatively, drop the data directory and use the backup
!rm -fr backup

"""## Geocoding Transform"""

# use the original Sentinel-1 resolution (1 pixel spacing)
sbas.compute_geocode(1)

sbas.plot_topo(quantile=[0.01, 0.99])

"""## Persistent Scatterers Function (PSF)"""

# use the only selected dates for the pixels stability analysis
sbas.compute_ps()

sbas.plot_psfunction(quantile=[0.01, 0.90])

psmask_sbas = sbas.multilooking(sbas.psfunction(), coarsen=(1,4), wavelength=100)>0.5
topo_sbas = sbas.get_topo().interp_like(psmask_sbas, method='nearest')
landmask_sbas = psmask_sbas&(np.isfinite(topo_sbas))
landmask_sbas = utils.binary_opening(landmask_sbas, structure=np.ones((20,20)))
landmask_sbas = np.isfinite(sbas.conncomp_main(landmask_sbas))
landmask_sbas = utils.binary_closing(landmask_sbas, structure=np.ones((20,20)))
landmask_sbas = np.isfinite(psmask_sbas.where(landmask_sbas))
sbas.plot_landmask(landmask_sbas)

"""## SBAS Baseline"""

baseline_pairs = sbas.sbas_pairs(days=60)
# optionally, drop dates having less then 2 pairs
#baseline_pairs = sbas.sbas_pairs_limit(baseline_pairs, limit=2, iterations=2)
# optionally, drop all pairs connected to the specified dates
#baseline_pairs = sbas.sbas_pairs_filter_dates(baseline_pairs, ['2021-01-01'])
baseline_pairs

with mpl_settings({'figure.dpi': 300}):
    sbas.plot_baseline(baseline_pairs)

"""## SBAS Analysis

### Multi-looked Resolution for SBAS
"""

sbas.compute_interferogram_multilook(baseline_pairs, 'intf_mlook', wavelength=200, psize=32,
                                     weight=sbas.psfunction())

# optionally, materialize to disk and open
ds_sbas = sbas.open_stack('intf_mlook')
# apply land mask
ds_sbas = ds_sbas.where(landmask_sbas)
intf_sbas = ds_sbas.phase
corr_sbas = ds_sbas.correlation
corr_sbas

sbas.plot_interferograms(intf_sbas[:8], caption='SBAS Phase, [rad]')

sbas.plot_correlations(corr_sbas[:8], caption='SBAS Correlation')

"""### Quality Check"""

#baseline_pairs['corr'] = corr_sbas.sel(pair=baseline_pairs.pair.values).mean(['y', 'x'])
baseline_pairs['corr'] = corr_sbas.mean(['y', 'x'])
print (len(baseline_pairs))
baseline_pairs

pairs_best = sbas.sbas_pairs_covering_correlation(baseline_pairs, 2)
print (len(pairs_best))
pairs_best

with mpl_settings({'figure.dpi': 300}):
    sbas.plot_baseline(pairs_best)

sbas.plot_baseline_correlation(baseline_pairs, pairs_best)

sbas.plot_baseline_duration(baseline_pairs, column='corr', ascending=False)

sbas.plot_baseline_duration(pairs_best, column='corr', ascending=False)

intf_sbas = intf_sbas.sel(pair=pairs_best.pair.values)
corr_sbas = corr_sbas.sel(pair=pairs_best.pair.values)

sbas.plot_interferograms(intf_sbas[:8], caption='SBAS Phase, [rad]')

sbas.plot_correlations(corr_sbas[:8], caption='SBAS Correlation')

"""### 2D Unwrapping"""

corr_sbas_stack = corr_sbas.mean('pair')

corr_sbas_stack = sbas.sync_cube(corr_sbas_stack, 'corr_sbas_stack')

sbas.plot_correlation_stack(corr_sbas_stack, CORRLIMIT := 0.3, caption='SBAS Stack Correlation')

sbas.plot_interferograms(intf_sbas[:8].where(corr_sbas_stack>CORRLIMIT), caption='SBAS Phase, [rad]')

unwrap_sbas = sbas.unwrap_snaphu(
    intf_sbas.where(corr_sbas_stack>CORRLIMIT),
    corr_sbas,
    conncomp=True
)
unwrap_sbas

# optionally, materialize to disk and open
unwrap_sbas = sbas.sync_cube(unwrap_sbas, 'unwrap_sbas')

sbas.plot_phases((unwrap_sbas.phase - unwrap_sbas.phase.mean(['y','x']))[:8], caption='SBAS Phase, [rad]')

# select the main valid component
unwrap_sbas = sbas.conncomp_main(unwrap_sbas, 1)

sbas.plot_phases((unwrap_sbas.phase - unwrap_sbas.phase.mean(['y','x']))[:8], caption='SBAS Phase, [rad]')

"""### Trend Correction"""

decimator_sbas = sbas.decimator(resolution=15, grid=(1,1))
topo = decimator_sbas(sbas.get_topo())
yy, xx = xr.broadcast(topo.y, topo.x)
trend_sbas = sbas.regression(unwrap_sbas.phase,
        [topo,    topo*yy,    topo*xx,    topo*yy*xx,
         topo**2, topo**2*yy, topo**2*xx, topo**2*yy*xx,
         yy, xx, yy*xx], corr_sbas)

# optionally, materialize to disk and open
trend_sbas = sbas.sync_cube(trend_sbas, 'trend_sbas')

sbas.plot_phases(trend_sbas[:8], caption='SBAS Trend Phase, [rad]', quantile=[0.01, 0.99])

sbas.plot_phases((unwrap_sbas.phase - trend_sbas)[:8], caption='SBAS Phase - Trend, [rad]', vmin=-np.pi, vmax=np.pi)

"""### Coherence-Weighted Least-Squares Solution for LOS Displacement, mm"""

# calculate phase displacement in radians and convert to LOS displacement in millimeter
disp_sbas = sbas.los_displacement_mm(sbas.lstsq(unwrap_sbas.phase - trend_sbas, corr_sbas))

# optionally, materialize to disk and open
disp_sbas = sbas.sync_cube(disp_sbas, 'disp_sbas')

sbas.plot_displacements(disp_sbas[::3], caption='SBAS Cumulative LOS Displacement, [mm]',
                        quantile=[0.01, 0.99], symmetrical=True)

"""### STL model for LOS Displacement, mm"""

stl_sbas = sbas.stl(disp_sbas)
stl_sbas

# optionally, materialize to disk and open
stl_sbas = sbas.sync_cube(stl_sbas, 'stl_sbas')

years = ((stl_sbas.date.max() - stl_sbas.date.min()).dt.days/365.25).item()
print ('years', np.round(years, 3))
velocity_sbas = stl_sbas.trend.mean('date')/years
velocity_sbas

fig = plt.figure(figsize=(12,4), dpi=300)

zmin, zmax = np.nanquantile(velocity_sbas, [0.01, 0.99])
zminmax = max(abs(zmin), zmax)
zmin = -zminmax
zmax =  zminmax

ax = fig.add_subplot(1, 2, 1)
velocity_sbas.plot.imshow(cmap='turbo', vmin=zmin, vmax=zmax, ax=ax)
sbas.geocode(AOI.boundary).plot(ax=ax)
sbas.geocode(POI).plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
ax.set_aspect('auto')
ax.set_title('Velocity, mm/year', fontsize=16)

ax = fig.add_subplot(1, 2, 2)
sbas.as_geo(sbas.ra2ll(velocity_sbas)).rio.clip(AOI.geometry)\
    .plot.imshow(cmap='turbo', vmin=zmin, vmax=zmax, ax=ax)
AOI.boundary.plot(ax=ax)
POI.plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
ax.legend(loc='upper left', fontsize=14)
ax.set_title('Velocity, mm/year', fontsize=16)

plt.suptitle('SBAS LOS Velocity STL Decompose, 2021', fontsize=18)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 4), dpi=300)

x, y = [(geom.x.item(), geom.y.item()) for geom in sbas.geocode(POI).geometry][0]
disp_pixel = disp_sbas.sel(y=y, x=x, method='nearest')
stl_pixel = stl_sbas.sel(y=y, x=x, method='nearest')
plt.plot(disp_pixel.date, disp_pixel, c='r', lw=2, label='Displacement POI')
plt.plot(stl_pixel.date, stl_pixel.trend, c='r', ls='--', lw=2, label='Trend POI')
plt.plot(stl_pixel.date, stl_pixel.seasonal, c='r', lw=1, label='Seasonal POI')

plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, fontsize=14)
plt.title('SBAS LOS Displacement STL Decompose, 2021', fontsize=18)
plt.ylabel('Displacement, mm', fontsize=16)
plt.show()

"""## PS Analysis

Use the trend detected on possibly lower resolution unwrapped phases for higher resolution analysis.
"""

stability = sbas.psfunction()
landmask_ps = landmask_sbas.astype(int).interp_like(stability, method='nearest').astype(bool)
sbas.compute_interferogram_singlelook(pairs_best, 'intf_slook', wavelength=60,
                                      weight=stability.where(landmask_ps), phase=trend_sbas)

# optionally, materialize to disk and open
ds_ps = sbas.open_stack('intf_slook')
intf_ps = ds_ps.phase
corr_ps = ds_ps.correlation

sbas.plot_interferograms(intf_ps[:8], caption='PS Phase, [rad]')

sbas.plot_correlations(corr_ps[:8], caption='PS Correlation')

"""### 1D Unwrapping and LOS Displacement, mm"""

disp_ps_pairs = sbas.los_displacement_mm(sbas.unwrap1d(intf_ps))
disp_ps_pairs

# optionally, materialize to disk and open
disp_ps_pairs = sbas.sync_cube(disp_ps_pairs, 'disp_ps_pairs')

"""### Coherence-Weighted Least-Squares Solution for LOS Displacement, mm"""

disp_ps = sbas.lstsq(disp_ps_pairs, corr_ps)
disp_ps

# optionally, materialize to disk and open
disp_ps = sbas.sync_cube(disp_ps, 'disp_ps')

sbas.plot_displacements(disp_ps[::3], caption='PS Cumulative LOS Displacement, [mm]',
                        quantile=[0.01, 0.99], symmetrical=True)

"""### STL model for LOS Displacement, mm"""

stl_ps = sbas.stl(disp_ps)
stl_ps

# optionally, materialize to disk and open
stl_ps = sbas.sync_cube(stl_ps, 'stl_ps')

years = ((stl_ps.date.max() - stl_ps.date.min()).dt.days/365.25).item()
print ('years', np.round(years, 3))
velocity_ps = stl_ps.trend.mean('date')/years
velocity_ps

fig = plt.figure(figsize=(12,4), dpi=300)

zmin, zmax = np.nanquantile(velocity_ps, [0.01, 0.99])
zminmax = max(abs(zmin), zmax)
zmin = -zminmax
zmax =  zminmax

ax = fig.add_subplot(1, 2, 1)
velocity_ps.plot.imshow(cmap='turbo', vmin=zmin, vmax=zmax, ax=ax)
sbas.geocode(AOI.boundary).plot(ax=ax)
sbas.geocode(POI).plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
ax.set_aspect('auto')
ax.set_title('Velocity, mm/year', fontsize=16)

ax = fig.add_subplot(1, 2, 2)
sbas.as_geo(sbas.ra2ll(velocity_ps)).rio.clip(AOI.geometry)\
    .plot.imshow(cmap='turbo', vmin=zmin, vmax=zmax, ax=ax)
AOI.boundary.plot(ax=ax)
POI.plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
ax.legend(loc='upper left', fontsize=14)
ax.set_title('Velocity, mm/year', fontsize=16)

plt.suptitle('PS LOS Velocity STL Decompose, 2021', fontsize=18)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 4), dpi=300)

x, y = [(geom.x.item(), geom.y.item()) for geom in sbas.geocode(POI).geometry][0]
disp_pixel = disp_ps.sel(y=y, x=x, method='nearest')
stl_pixel = stl_ps.sel(y=y, x=x, method='nearest')
plt.plot(disp_pixel.date, disp_pixel, c='r', lw=2, label='Displacement POI')
plt.plot(stl_pixel.date, stl_pixel.trend, c='r', ls='--', lw=2, label='Trend POI')
plt.plot(stl_pixel.date, stl_pixel.seasonal, c='r', lw=1, label='Seasonal POI')

plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, fontsize=14)
plt.title('PS LOS Displacement STL Decompose, 2021', fontsize=18)
plt.ylabel('Displacement, mm', fontsize=16)
plt.show()

x, y = [(geom.x.item(), geom.y.item()) for geom in sbas.geocode(POI).geometry][0]
sbas.plot_baseline_displacement(disp_ps_pairs.sel(y=y, x=x, method='nearest')/sbas.los_displacement_mm(1),
                                corr_ps.sel(y=y, x=x, method='nearest'),
                               caption='POI', stl=True)

rmse = sbas.rmse(disp_ps_pairs, disp_ps, corr_ps)
rmse

sbas.plot_rmse(rmse)

"""## SBAS vs PS Comparision"""

# crop AOI
points_sbas = sbas.as_geo(sbas.ra2ll(velocity_sbas)).rio.clip(AOI.geometry)
points_ps = sbas.as_geo(sbas.ra2ll(velocity_ps)).rio.clip(AOI.geometry)
points_ps = points_ps.interp_like(points_sbas, method='nearest').values.ravel()
points_sbas = points_sbas.values.ravel()
nanmask = np.isnan(points_sbas) | np.isnan(points_ps)
points_sbas = points_sbas[~nanmask]
points_ps = points_ps[~nanmask]

plt.figure(figsize=(12, 4), dpi=300)
plt.scatter(points_sbas, points_ps, c='silver', alpha=1,   s=1)
plt.scatter(points_sbas, points_ps, c='b',      alpha=0.1, s=1)
plt.scatter(points_sbas, points_ps, c='g',      alpha=0.1, s=0.1)
plt.scatter(points_sbas, points_ps, c='y',      alpha=0.1, s=0.01)

# adding a 1:1 line
max_value = max(velocity_sbas.max(), velocity_ps.max())
min_value = min(velocity_sbas.min(), velocity_ps.min())
plt.plot([min_value, max_value], [min_value, max_value], 'k--')

plt.xlabel('Velocity SBAS, mm/year', fontsize=16)
plt.ylabel('Velocity PS, mm/years', fontsize=16)
plt.title('Cross-Comparison between SBAS and PS Velocity', fontsize=18)
plt.grid(True)
plt.show()

"""## 3D Interactive Map"""

dem = sbas.get_dem()

velocity_sbas_ll = sbas.ra2ll(velocity_sbas)
velocity_ps_ll = sbas.ra2ll(velocity_ps)

velocity_sbas_ll = sbas.as_geo(velocity_sbas_ll).rio.clip(AOI.geometry.envelope)
velocity_ps_ll = sbas.as_geo(velocity_ps_ll).rio.clip(AOI.geometry.envelope)

gmap_tiles = XYZTiles().download(velocity_sbas_ll, 15)

for name, velocity_ll in {'sbas': velocity_sbas_ll, 'ps': velocity_ps_ll}.items():
    gmap = gmap_tiles.interp_like(velocity_ll, method='cubic').round().astype(np.uint8)
    ds = xr.merge([dem.interp_like(velocity_ll, method='cubic').rename('z'), gmap, velocity_ll])
    # decimate large grid
    if name == 'sbas':
        ds = ds.sel(lat=ds.lat[::3], lon=ds.lon[::2])
    else:
        ds = ds.sel(lat=ds.lat[::3], lon=ds.lon[::8])
    # convert to VTK structure
    vtk_grid = pv.StructuredGrid(NCubeVTK.ImageOnTopography(ds.rename({'lat': 'y', 'lon': 'x'})))
    vtk_grid.save(f'velocity_{name}.vtk')
    print (vtk_grid)

plotter = pv.Plotter(shape=(1, 2), notebook=True)
axes = pv.Axes(show_actor=True, actor_scale=2.0, line_width=5)

plotter.subplot(0, 0)
vtk_grid = pv.read('velocity_sbas.vtk')
mesh = vtk_grid.scale([1, 1, 0.00001]).rotate_z(135, point=axes.origin)
plotter.add_mesh(mesh.scale([1, 1, 0.999]), scalars='colors', rgb=True, ambient=0.2)
plotter.add_mesh(mesh, scalars='trend', ambient=0.2, cmap='turbo', clim=(-60,60), nan_opacity=0.1, nan_color='black')
plotter.show_axes()
plotter.add_title('SBAS LOS Velocity', font_size=32)

plotter.subplot(0, 1)
vtk_grid = pv.read('velocity_ps.vtk')
mesh = vtk_grid.scale([1, 1, 0.00001]).rotate_z(135, point=axes.origin)
plotter.add_mesh(mesh.scale([1, 1, 0.999]), scalars='colors', rgb=True, ambient=0.2)
plotter.add_mesh(mesh, scalars='trend', ambient=0.2, cmap='turbo', clim=(-60,60), nan_opacity=0.1, nan_color='black')
plotter.show_axes()
plotter.add_title('PS LOS Velocity', font_size=32)

plotter.show_axes()
plotter._on_first_render_request()
panel.panel(
    plotter.render_window, orientation_widget=plotter.renderer.axes_enabled,
    enable_keybindings=False, sizing_mode='stretch_width', min_height=600
)

"""## Export VTK file from Google Colab"""

if 'google.colab' in sys.modules:
    from google.colab import files
    files.download('velocity_sbas.vtk')
    files.download('velocity_ps.vtk')