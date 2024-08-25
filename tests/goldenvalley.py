# -*- coding: utf-8 -*-
"""GoldenValley.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ipiQGbvUF8duzjZER8v-_R48DSpSmgvQ

## PyGMTSAR SBAS and PSI Analyses: Golden Valley, CA

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

## Google Colab Installation

Install PyGMTSAR and required GMTSAR binaries (including SNAPHU)
"""

# Commented out IPython magic to ensure Python compatibility.
import platform, sys, os
if 'google.colab' in sys.modules:
    # install PyGMTSAR stable version from PyPI
    !{sys.executable} -m pip install -q pygmtsar
    # alternatively, nstall PyGMTSAR development version from GitHub
    #!{sys.executable} -m pip install -Uq git+https://github.com/mobigroup/gmtsar.git@pygmtsar2#subdirectory=pygmtsar
    # use PyGMTSAR Google Colab installation script to install binary dependencies
    # script URL: https://github.com/AlexeyPechnikov/pygmtsar/blob/pygmtsar2/pygmtsar/pygmtsar/data/google_colab.sh
    import importlib.resources as resources
    with resources.as_file(resources.files('pygmtsar.data') / 'google_colab.sh') as google_colab_script_filename:
        !sh {google_colab_script_filename}
    # enable custom widget manager as required by recent Google Colab updates
    from google.colab import output
    output.enable_custom_widget_manager()
    # initialize virtual framebuffer for interactive 3D visualization; required for headless environments
    import xvfbwrapper
    display = xvfbwrapper.Xvfb(width=800, height=600)
    display.start()

# specify GMTSAR installation path
PATH = os.environ['PATH']
if PATH.find('GMTSAR') == -1:
    PATH = os.environ['PATH'] + ':/usr/local/GMTSAR/bin/'
#     %env PATH {PATH}

# display PyGMTSAR version
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
panel.extension(comms='ipywidgets')
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

from pygmtsar import S1, Stack, tqdm_dask, ASF, Tiles, XYZTiles

"""## Define Sentinel-1 SLC Scenes and Processing Parameters

### Descending Orbit Configuration
"""

# The subswath is required for partial scene downloads and is not used for burst downloads.
# The orbit is used to define directory names.
ORBIT     = 'D'
SUBSWATH  = 3
REFERENCE = '2021-07-05'

"""https://search.asf.alaska.edu/#/?polygon=POLYGON((-118.4711%2034.3916,-118.47%2034.3915,-118.4688%2034.3916,-118.467%2034.3921,-118.4658%2034.3924,-118.4646%2034.3928,-118.4629%2034.3936,-118.461%2034.3942,-118.4578%2034.3939,-118.4595%2034.399,-118.46%2034.3994,-118.4631%2034.3976,-118.4674%2034.3952,-118.469%2034.394,-118.4699%2034.3934,-118.471%2034.3926,-118.4717%2034.3918,-118.4711%2034.3916))&start=2021-01-05T17:00:00Z&end=2021-12-20T16:59:59Z&resultsLoaded=true&granule=S1A_IW_SLC__1SDV_20211208T135244_20211208T135312_040918_04DBF1_5BB3-SLC&productTypes=SLC&flightDirs=Descending&zoom=7.663&center=-117.645,32.567&path=71-71&frame=480-480"""

# SCENES = """
# S1A_IW_SLC__1SDV_20211220T135243_20211220T135311_041093_04E1C6_571D
# S1A_IW_SLC__1SDV_20211208T135244_20211208T135312_040918_04DBF1_5BB3
# S1A_IW_SLC__1SDV_20211126T135244_20211126T135312_040743_04D5D8_F7BC
# S1A_IW_SLC__1SDV_20211114T135245_20211114T135313_040568_04CFD7_582A
# S1A_IW_SLC__1SDV_20211102T135245_20211102T135313_040393_04C9B8_06BA
# S1A_IW_SLC__1SDV_20211021T135246_20211021T135313_040218_04C3A1_AC92
# S1A_IW_SLC__1SDV_20211009T135246_20211009T135313_040043_04BD89_8A1C
# S1A_IW_SLC__1SDV_20210927T135246_20210927T135313_039868_04B77E_080A
# S1A_IW_SLC__1SDV_20210915T135245_20210915T135312_039693_04B182_B51B
# S1A_IW_SLC__1SDV_20210903T135245_20210903T135312_039518_04AB89_6CBC
# S1A_IW_SLC__1SDV_20210822T135244_20210822T135311_039343_04A583_7922
# S1A_IW_SLC__1SDV_20210810T135244_20210810T135311_039168_049F83_A317
# S1A_IW_SLC__1SDV_20210729T135243_20210729T135310_038993_0499C7_1A1B
# S1A_IW_SLC__1SDV_20210717T135242_20210717T135309_038818_049496_0ABE
# S1A_IW_SLC__1SDV_20210705T135242_20210705T135309_038643_048F59_0F30
# S1A_IW_SLC__1SDV_20210623T135241_20210623T135308_038468_048A0E_7E2B
# S1A_IW_SLC__1SDV_20210611T135240_20210611T135307_038293_0484D8_D775
# S1A_IW_SLC__1SDV_20210530T135240_20210530T135306_038118_047FAA_A70D
# S1A_IW_SLC__1SDV_20210518T135239_20210518T135306_037943_047A68_660C
# S1A_IW_SLC__1SDV_20210506T135238_20210506T135305_037768_047520_2C81
# S1A_IW_SLC__1SDV_20210424T135238_20210424T135305_037593_046F1A_82DC
# S1A_IW_SLC__1SDV_20210412T135237_20210412T135304_037418_046911_7DB6
# S1A_IW_SLC__1SDV_20210331T135237_20210331T135304_037243_046307_91F1
# S1A_IW_SLC__1SDV_20210319T135236_20210319T135303_037068_045CFB_34F9
# S1A_IW_SLC__1SDV_20210307T135236_20210307T135303_036893_0456E2_0C1D
# S1A_IW_SLC__1SDV_20210223T135236_20210223T135303_036718_0450C6_883C
# S1A_IW_SLC__1SDV_20210211T135237_20210211T135304_036543_044AAA_DAE0
# S1A_IW_SLC__1SDV_20210130T135237_20210130T135304_036368_04449D_30E3
# S1A_IW_SLC__1SDV_20210118T135237_20210118T135304_036193_043E88_5815
# S1A_IW_SLC__1SDV_20210106T135238_20210106T135305_036018_043864_D0B4
# """
# SCENES = list(filter(None, SCENES.split('\n')))
# print (f'Scenes defined: {len(SCENES)}')

"""https://search.asf.alaska.edu/#/?polygon=POLYGON((-118.4711%2034.3916,-118.47%2034.3915,-118.4688%2034.3916,-118.467%2034.3921,-118.4658%2034.3924,-118.4646%2034.3928,-118.4629%2034.3936,-118.461%2034.3942,-118.4578%2034.3939,-118.4595%2034.399,-118.46%2034.3994,-118.4631%2034.3976,-118.4674%2034.3952,-118.469%2034.394,-118.4699%2034.3934,-118.471%2034.3926,-118.4717%2034.3918,-118.4711%2034.3916))&start=2021-01-05T17:00:00Z&end=2021-12-20T16:59:59Z&resultsLoaded=true&granule=S1_151226_IW3_20211220T135244_VV_571D-BURST&flightDirs=Descending&zoom=9.794&center=-118.575,34.110&path=71-71&frame=480-480&dataset=SENTINEL-1%20BURSTS&polarizations=VV"""

BURSTS = """
S1_151226_IW3_20211220T135244_VV_571D-BURST
S1_151226_IW3_20211208T135245_VV_5BB3-BURST
S1_151226_IW3_20211126T135245_VV_F7BC-BURST
S1_151226_IW3_20211114T135246_VV_582A-BURST
S1_151226_IW3_20211102T135246_VV_06BA-BURST
S1_151226_IW3_20211021T135246_VV_AC92-BURST
S1_151226_IW3_20211009T135246_VV_8A1C-BURST
S1_151226_IW3_20210927T135246_VV_080A-BURST
S1_151226_IW3_20210915T135245_VV_B51B-BURST
S1_151226_IW3_20210903T135245_VV_6CBC-BURST
S1_151226_IW3_20210822T135244_VV_7922-BURST
S1_151226_IW3_20210810T135244_VV_A317-BURST
S1_151226_IW3_20210729T135243_VV_1A1B-BURST
S1_151226_IW3_20210717T135242_VV_0ABE-BURST
S1_151226_IW3_20210705T135242_VV_0F30-BURST
S1_151226_IW3_20210623T135241_VV_7E2B-BURST
S1_151226_IW3_20210611T135240_VV_D775-BURST
S1_151226_IW3_20210530T135240_VV_A70D-BURST
S1_151226_IW3_20210518T135239_VV_660C-BURST
S1_151226_IW3_20210506T135238_VV_2C81-BURST
S1_151226_IW3_20210424T135238_VV_82DC-BURST
S1_151226_IW3_20210412T135237_VV_7DB6-BURST
S1_151226_IW3_20210331T135237_VV_91F1-BURST
S1_151226_IW3_20210319T135236_VV_34F9-BURST
S1_151226_IW3_20210307T135236_VV_0C1D-BURST
S1_151226_IW3_20210223T135236_VV_883C-BURST
S1_151226_IW3_20210211T135237_VV_DAE0-BURST
S1_151226_IW3_20210130T135237_VV_30E3-BURST
S1_151226_IW3_20210118T135237_VV_5815-BURST
S1_151226_IW3_20210106T135238_VV_D0B4-BURST
"""
BURSTS = list(filter(None, BURSTS.split('\n')))
print (f'Bursts defined: {len(BURSTS)}')

# select the only 1A satellite bursts corresponding to the scenes above
# import re
# scene_dates = [re.search(r'\d{8}T\d{6}', scene).group(0)[:8] for scene in SCENES]
# burst_dates = [re.search(r'\d{8}T\d{6}', burst).group(0)[:8] for burst in BURSTS]
# matching_bursts = [burst for burst in BURSTS if any(date in burst for date in scene_dates)]
# for burst in matching_bursts: print (burst)

WORKDIR = 'raw_golden_desc'  if ORBIT == 'D' else 'raw_golden_asc'
DATADIR = 'data_golden_desc' if ORBIT == 'D' else 'data_golden_asc'

# define DEM and landmask filenames inside data directory
DEM = f'{DATADIR}/dem.nc'

geojson = '''
{
  "type": "Feature",
  "properties": {},
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-118.4711, 34.3916],
        [-118.47, 34.3915],
        [-118.4688, 34.3916],
        [-118.467, 34.3921],
        [-118.4658, 34.3924],
        [-118.4646, 34.3928],
        [-118.4629, 34.3936],
        [-118.461, 34.3942],
        [-118.4578, 34.3939],
        [-118.4595, 34.399],
        [-118.46, 34.3994],
        [-118.4631, 34.3976],
        [-118.4674, 34.3952],
        [-118.469, 34.394],
        [-118.4699, 34.3934],
        [-118.471, 34.3926],
        [-118.4717, 34.3918],
        [-118.4711, 34.3916]
      ]
    ]
  }
}
'''
AOI = gpd.GeoDataFrame.from_features([json.loads(geojson)])
AOI

BUFFER = 0.025
# geometry is too small for the processing, enlarge it
AOI['geometry'] = AOI.buffer(BUFFER)

# subsidence point from https://blog.descarteslabs.com/sentinel-1-targeted-analysis
geojson = '''
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-118.4652, 34.3952]
  },
  "properties": {}
}
'''
POI = gpd.GeoDataFrame.from_features([json.loads(geojson)])
POI

# reference point from https://blog.descarteslabs.com/sentinel-1-targeted-analysis
geojson = '''
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-118.4629,34.3946]
  },
  "properties": {}
}
'''
POI0 = gpd.GeoDataFrame.from_features([json.loads(geojson)])
POI0

"""## Download and Unpack Datasets

## Enter Your ASF User and Password

If the data directory is empty or doesn't exist, you'll need to download Sentinel-1 scenes from the Alaska Satellite Facility (ASF) datastore. Use your Earthdata Login credentials. If you don't have an Earthdata Login, you can create one at https://urs.earthdata.nasa.gov//users/new

You can also use pre-existing SLC scenes stored on your Google Drive, or you can copy them using a direct public link from iCloud Drive.

The credentials below are available at the time the notebook is validated.
"""

# Set these variables to None and you will be prompted to enter your username and password below.
asf_username = 'GoogleColab2023'
asf_password = 'GoogleColab_2023'

# Set these variables to None and you will be prompted to enter your username and password below.
asf = ASF(asf_username, asf_password)
# Optimized scene downloading from ASF - only the required subswaths and polarizations.
# Subswaths are already encoded in burst identifiers and are only needed for scenes.
#print(asf.download(DATADIR, SCENES, SUBSWATH))
print(asf.download(DATADIR, BURSTS))

# scan the data directory for SLC scenes and download missed orbits
S1.download_orbits(DATADIR, S1.scan_slc(DATADIR))

# download NASA SRTM DEM 1 arc-second
Tiles().download_dem_srtm(AOI, filename=DEM).plot.imshow(cmap='cividis')

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

"""## Geocoding Transform"""

# use the original Sentinel-1 resolution (1 pixel spacing)
sbas.compute_geocode(1)

sbas.plot_topo(quantile=[0.01, 0.99])

"""## SBAS Baseline"""

baseline_pairs = sbas.sbas_pairs(days=24)
# optionally, drop dates having less then 2 pairs
#baseline_pairs = sbas.sbas_pairs_limit(baseline_pairs, limit=2, iterations=2)
# optionally, drop all pairs connected to the specified dates
#baseline_pairs = sbas.sbas_pairs_filter_dates(baseline_pairs, ['2021-01-01'])
baseline_pairs

with mpl_settings({'figure.dpi': 300}):
    sbas.plot_baseline(baseline_pairs)

"""## Persistent Scatterers Function (PSF)"""

# use the only selected dates for the pixels stability analysis
sbas.compute_ps()

sbas.plot_psfunction(quantile=[0.01, 0.90])

"""## SBAS Analysis

### Multi-looked Resolution for SBAS
"""

sbas.compute_interferogram_multilook(baseline_pairs, 'intf_mlook', wavelength=30, weight=sbas.psfunction())

# optionally, materialize to disk and open
ds_sbas = sbas.open_stack('intf_mlook')
intf_sbas = ds_sbas.phase
corr_sbas = ds_sbas.correlation
corr_sbas

intf_sbas

sbas.plot_interferograms(intf_sbas[:8], caption='SBAS Phase, [rad]')

sbas.plot_correlations(corr_sbas[:8], caption='SBAS Correlation')

"""### 2D Unwrapping"""

unwrap_sbas = sbas.unwrap_snaphu(intf_sbas, corr_sbas)
unwrap_sbas

# optionally, materialize to disk and open
unwrap_sbas = sbas.sync_cube(unwrap_sbas, 'unwrap_sbas')

sbas.plot_phases(unwrap_sbas.phase[:8], caption='SBAS Phase, [rad]')

"""### Trend Correction"""

decimator = sbas.decimator(resolution=15, grid=(1,1))
topo = decimator(sbas.get_topo())
inc = decimator(sbas.incidence_angle())
yy, xx = xr.broadcast(topo.y, topo.x)
trend_sbas = sbas.regression(unwrap_sbas.phase,
        [topo,    topo*yy,    topo*xx,    topo*yy*xx,
         topo**2, topo**2*yy, topo**2*xx, topo**2*yy*xx,
         topo**3, topo**3*yy, topo**3*xx, topo**3*yy*xx,
         inc,     inc**yy,    inc*xx,     inc*yy*xx,
         yy, xx,
         yy**2, xx**2, yy*xx,
         yy**3, xx**3, yy**2*xx, xx**2*yy], corr_sbas)

# optionally, materialize to disk and open
trend_sbas = sbas.sync_cube(trend_sbas, 'trend_sbas')

sbas.plot_phases(trend_sbas[:8], caption='SBAS Trend Phase, [rad]', quantile=[0.01, 0.99])

sbas.plot_phases((unwrap_sbas.phase - trend_sbas)[:8], caption='SBAS Phase - Trend, [rad]', vmin=-np.pi, vmax=np.pi)

"""### Coherence-Weighted Least-Squares Solution for LOS Displacement, mm"""

# calculate phase displacement in radians and convert to LOS displacement in millimeter
disp_sbas = sbas.los_displacement_mm(sbas.lstsq(unwrap_sbas.phase - trend_sbas, corr_sbas))

# optionally, materialize to disk and open
disp_sbas = sbas.sync_cube(disp_sbas, 'disp_sbas')

sbas.plot_displacements(disp_sbas[::3], caption='SBAS Cumulative LOS Displacement, [mm]', quantile=[0.01, 0.99])

"""### Least-squares model for LOS Displacement, mm"""

velocity_sbas = sbas.velocity(disp_sbas)
velocity_sbas

# optionally, materialize to disk and open
velocity_sbas = sbas.sync_cube(velocity_sbas, 'velocity_sbas')

fig = plt.figure(figsize=(12,4), dpi=300)

zmin, zmax = np.nanquantile(velocity_sbas, [0.01, 0.99])
zminmax = max(abs(zmin), zmax)

ax = fig.add_subplot(1, 2, 1)
velocity_sbas.plot.imshow(cmap='turbo', vmin=-zminmax, vmax=zminmax, ax=ax)
sbas.geocode(AOI.buffer(-BUFFER).boundary).plot(ax=ax)
sbas.geocode(POI).plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
sbas.geocode(POI0).plot(ax=ax, marker='x', c='b', markersize=100, label='POI$\Theta$')
ax.set_aspect('auto')
ax.set_title('Velocity, mm/year', fontsize=16)

ax = fig.add_subplot(1, 2, 2)
sbas.as_geo(sbas.ra2ll(velocity_sbas)).rio.clip(AOI.geometry.buffer(-BUFFER))\
    .plot.imshow(cmap='turbo', vmin=-zminmax, vmax=zminmax, ax=ax)
AOI.buffer(-BUFFER).boundary.plot(ax=ax)
POI.plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
POI0.plot(ax=ax, marker='x', c='b', markersize=100, label='POI$\Theta$')
ax.legend(loc='upper left', fontsize=14)
ax.set_title('Velocity, mm/year', fontsize=16)

plt.suptitle('SBAS LOS Velocity, 2021', fontsize=18)
plt.tight_layout()
plt.show()

"""### STL model for LOS Displacement, mm"""

plt.figure(figsize=(12, 4), dpi=300)

x, y = [(geom.x, geom.y) for geom in sbas.geocode(POI).geometry][0]
disp_pixel = disp_sbas.sel(y=y, x=x, method='nearest')
stl_pixel = sbas.stl(disp_sbas.sel(y=[y], x=[x], method='nearest')).isel(x=0, y=0)
plt.plot(disp_pixel.date, disp_pixel, c='r', lw=2, label='Displacement POI')
plt.plot(stl_pixel.date, stl_pixel.trend, c='r', ls='--', lw=2, label='Trend POI')
plt.plot(stl_pixel.date, stl_pixel.seasonal, c='r', lw=1, label='Seasonal POI')

x, y = [(geom.x, geom.y) for geom in sbas.geocode(POI0).geometry][0]
disp_pixel = disp_sbas.sel(y=y, x=x, method='nearest')
stl_pixel = sbas.stl(disp_sbas.sel(y=[y], x=[x], method='nearest')).isel(x=0, y=0)
plt.plot(disp_pixel.date, disp_pixel, c='b', lw=2, label='Displacement POI$\Theta$')
plt.plot(stl_pixel.date, stl_pixel.trend, c='b', ls='--', lw=2, label='Trend POI$\Theta$')
plt.plot(stl_pixel.date, stl_pixel.seasonal, c='b', lw=1, label='Seasonal POI$\Theta$')

plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, fontsize=14)
plt.title('SBAS LOS Displacement STL Decompose, 2021', fontsize=18)
plt.ylabel('Displacement, mm', fontsize=16)
plt.show()

"""## PS Analysis

Use the trend detected on possibly lower resolution unwrapped phases for higher resolution analysis.
"""

sbas.compute_interferogram_singlelook(baseline_pairs, 'intf_slook', wavelength=30,
                                      weight=sbas.psfunction(), phase=trend_sbas)

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

zmin, zmax = np.nanquantile(disp_ps, [0.01, 0.99])
sbas.plot_displacements(disp_ps[::3], caption='PS Cumulative LOS Displacement, [mm]', vmin=zmin, vmax=zmax)

"""### Least-squares model for LOS Displacement, mm"""

velocity_ps = sbas.velocity(disp_ps)
velocity_ps

# optionally, materialize to disk and open
velocity_ps = sbas.sync_cube(velocity_ps, 'velocity_ps')

fig = plt.figure(figsize=(12,4), dpi=300)

zmin, zmax = np.nanquantile(velocity_ps, [0.01, 0.99])
zminmax = max(abs(zmin), zmax)

ax = fig.add_subplot(1, 2, 1)
velocity_ps.plot.imshow(cmap='turbo', vmin=-zminmax, vmax=zminmax, ax=ax)
sbas.geocode(AOI.buffer(-BUFFER).boundary).plot(ax=ax)
sbas.geocode(POI).plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
sbas.geocode(POI0).plot(ax=ax, marker='x', c='b', markersize=100, label='POI$\Theta$')
ax.set_aspect('auto')
ax.set_title('Velocity, mm/year', fontsize=16)

ax = fig.add_subplot(1, 2, 2)
sbas.as_geo(sbas.ra2ll(velocity_ps)).rio.clip(AOI.geometry.buffer(-BUFFER))\
    .plot.imshow(cmap='turbo', vmin=-zminmax, vmax=zminmax, ax=ax)
AOI.buffer(-BUFFER).boundary.plot(ax=ax)
POI.plot(ax=ax, marker='x', c='r', markersize=100, label='POI')
POI0.plot(ax=ax, marker='x', c='b', markersize=100, label='POI$\Theta$')
ax.legend(loc='upper left', fontsize=14)
ax.set_title('Velocity, mm/year', fontsize=16)

plt.suptitle('PS LOS Velocity, 2021', fontsize=18)
plt.tight_layout()
plt.show()

"""### STL model for LOS Displacement, mm"""

plt.figure(figsize=(12, 4), dpi=300)

x, y = [(geom.x, geom.y) for geom in sbas.geocode(POI).geometry][0]
disp_pixel = disp_ps.sel(y=y, x=x, method='nearest')
stl_pixel = sbas.stl(disp_ps.sel(y=[y], x=[x], method='nearest')).isel(x=0, y=0)
plt.plot(disp_pixel.date, disp_pixel, c='r', lw=2, label='Displacement POI')
plt.plot(stl_pixel.date, stl_pixel.trend, c='r', ls='--', lw=2, label='Trend POI')
plt.plot(stl_pixel.date, stl_pixel.seasonal, c='r', lw=1, label='Seasonal POI')

x, y = [(geom.x, geom.y) for geom in sbas.geocode(POI0).geometry][0]
disp_pixel = disp_ps.sel(y=y, x=x, method='nearest')
stl_pixel = sbas.stl(disp_ps.sel(y=[y], x=[x], method='nearest')).isel(x=0, y=0)
plt.plot(disp_pixel.date, disp_pixel, c='b', lw=2, label='Displacement POI$\Theta$')
plt.plot(stl_pixel.date, stl_pixel.trend, c='b', ls='--', lw=2, label='Trend POI$\Theta$')
plt.plot(stl_pixel.date, stl_pixel.seasonal, c='b', lw=1, label='Seasonal POI$\Theta$')

plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, fontsize=14)
plt.title('PS LOS Displacement STL Decompose, 2021', fontsize=18)
plt.ylabel('Displacement, mm', fontsize=16)
plt.show()

x, y = [(geom.x, geom.y) for geom in sbas.geocode(POI0).geometry][0]
sbas.plot_baseline_displacement_los_mm(disp_ps_pairs.sel(y=y, x=x, method='nearest')/sbas.los_displacement_mm(1),
                                corr_ps.sel(y=y, x=x, method='nearest'),
                               caption='POI0', stl=True)

x, y = [(geom.x, geom.y) for geom in sbas.geocode(POI).geometry][0]
sbas.plot_baseline_displacement_los_mm(disp_ps_pairs.sel(y=y, x=x, method='nearest')/sbas.los_displacement_mm(1),
                                corr_ps.sel(y=y, x=x, method='nearest'),
                               caption='POI', stl=True)

"""### RMSE Error Estimation"""

rmse_ps = sbas.rmse(disp_ps_pairs, disp_ps, corr_ps)
rmse_ps

# optionally, materialize to disk and open
rmse_ps = sbas.sync_cube(rmse_ps, 'rmse_ps')

sbas.plot_rmse(rmse_ps, caption='RMSE Correlation Aware, [mm]')

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
plt.ylabel('Velocity PS, mm/year', fontsize=16)
plt.title('Cross-Comparison between SBAS and PS Velocity', fontsize=18)
plt.grid(True)
plt.show()

"""## 3D Interactive Map"""

velocity_sbas_ll = sbas.ra2ll(velocity_sbas)
velocity_ps_ll = sbas.ra2ll(velocity_ps)
# crop to area
velocity_sbas_ll = sbas.as_geo(velocity_sbas_ll).rio.clip(AOI.geometry.buffer(-BUFFER))
velocity_ps_ll = sbas.as_geo(velocity_ps_ll).rio.clip(AOI.geometry.buffer(-BUFFER))
# export VTK
sbas.export_vtk(velocity_sbas_ll, 'velocity_sbas', mask='auto')
sbas.export_vtk(velocity_ps_ll,   'velocity_ps', mask='auto')

gmap = XYZTiles().download(velocity_sbas_ll, 15)
gmap.plot.imshow()
sbas.export_vtk(None, 'gmap', image=gmap, mask='auto')

plotter = pv.Plotter(shape=(1, 2), notebook=True)
axes = pv.Axes(show_actor=True, actor_scale=2.0, line_width=5)

vtk_map = pv.read('gmap.vtk').scale([1, 1, 0.00002]).rotate_z(135)


plotter.subplot(0, 0)
vtk_grid = pv.read('velocity_sbas.vtk').scale([1, 1, 0.00002]).rotate_z(135)
plotter.add_mesh(vtk_map.scale([1, 1, 0.999]), scalars='colors', rgb=True, ambient=0.2)
plotter.add_mesh(vtk_grid, scalars='trend', ambient=0.5, opacity=0.8, cmap='turbo', clim=(-30,30), nan_opacity=0.1, nan_color='black')
plotter.show_axes()
plotter.add_title('SBAS LOS Velocity', font_size=32)

plotter.subplot(0, 1)
vtk_grid = pv.read('velocity_ps.vtk').scale([1, 1, 0.00002]).rotate_z(135)
plotter.add_mesh(vtk_map.scale([1, 1, 0.999]), scalars='colors', rgb=True, ambient=0.2)
plotter.add_mesh(vtk_grid, scalars='trend', ambient=0.5, opacity=0.8, cmap='turbo', clim=(-30,30), nan_opacity=0.1, nan_color='black')
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