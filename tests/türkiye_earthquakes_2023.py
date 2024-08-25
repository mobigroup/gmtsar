# -*- coding: utf-8 -*-
"""Türkiye_Earthquakes_2023.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TARVTB7z8goZyEVDRWyTAKJpyuqZxzW2

## PyGMTSAR Co-Seismic Interferogram: CENTRAL Türkiye Mw 7.8 & 7.5 Earthquakes, 2023

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
    !{sys.executable} -m pip install -q pygmtsar 'scipy==1.11.4'
    # alternatively, install PyGMTSAR development version from GitHub
    #!{sys.executable} -m pip install -Uq git+https://github.com/mobigroup/gmtsar.git@pygmtsar2#subdirectory=pygmtsar 'scipy==1.11.4'
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
import shapely
from dask.distributed import Client
import psutil
import dask

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
plt.rcParams['figure.dpi'] = 100
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

from pygmtsar import S1, Stack, tqdm_dask, ASF, Tiles

"""## Define Sentinel-1 SLC Scenes and Processing Parameters

When you need more scenes and SBAS analysis  see examples on PyGMTSAR GitHub page https://github.com/mobigroup/gmtsar

### Descending Orbit Configuration

https://search.asf.alaska.edu/#/?start=2023-01-19T17:00:00Z&resultsLoaded=true&granule=S1A_IW_SLC__1SDV_20230210T033451_20230210T033518_047168_05A8CD_E5B0-SLC&zoom=5.039&center=34.891,27.316&end=2023-02-10T16:59:59Z&productTypes=SLC&path=21-&frame=465-471
"""

POLARIZATION = 'VV'
ORBIT        = 'D'
SUBSWATH     = 123

# # Path 21 Frames 465 - 471
# SCENES = """
# S1A_IW_SLC__1SDV_20230129T033427_20230129T033455_046993_05A2FE_6FF2
# S1A_IW_SLC__1SDV_20230129T033452_20230129T033519_046993_05A2FE_BE0B
# S1A_IW_SLC__1SDV_20230210T033426_20230210T033454_047168_05A8CD_FAA6
# S1A_IW_SLC__1SDV_20230210T033451_20230210T033518_047168_05A8CD_E5B0
# """
# SCENES = list(filter(None, SCENES.split('\n')))
# print (f'Scenes defined: {len(SCENES)}')

"""https://search.asf.alaska.edu/#/?polygon=LINESTRING(35.7%2036,37%2038.8,36.7%2035.8,38.7%2038.5,38%2035.5)&searchType=Geographic%20Search&searchList=S1A_IW_SLC__1SDV_20230129T033427_20230129T033455_046993_05A2FE_6FF2,S1A_IW_SLC__1SDV_20230129T033452_20230129T033519_046993_05A2FE_BE0B,S1A_IW_SLC__1SDV_20230210T033426_20230210T033454_047168_05A8CD_FAA6,S1A_IW_SLC__1SDV_20230210T033451_20230210T033518_047168_05A8CD_E5B0&resultsLoaded=true&granule=S1_043820_IW1_20230129T033512_VV_BE0B-BURST&zoom=6.843&center=36.353,34.829&start=2023-01-28T17:00:00Z&end=2023-02-10T16:59:59Z&flightDirs=Descending&dataset=SENTINEL-1%20BURSTS&path=21-21&beamModes=IW&polarizations=VV"""

BURSTS = """
S1_043822_IW1_20230210T033516_VV_D767-BURST
S1_043821_IW3_20230210T033515_VV_E5B0-BURST
S1_043821_IW2_20230210T033514_VV_E5B0-BURST
S1_043821_IW1_20230210T033513_VV_E5B0-BURST
S1_043820_IW3_20230210T033513_VV_E5B0-BURST
S1_043820_IW2_20230210T033512_VV_E5B0-BURST
S1_043820_IW1_20230210T033511_VV_E5B0-BURST
S1_043819_IW3_20230210T033510_VV_E5B0-BURST
S1_043819_IW2_20230210T033509_VV_E5B0-BURST
S1_043819_IW1_20230210T033508_VV_E5B0-BURST
S1_043818_IW3_20230210T033507_VV_E5B0-BURST
S1_043818_IW2_20230210T033506_VV_E5B0-BURST
S1_043818_IW1_20230210T033505_VV_E5B0-BURST
S1_043817_IW3_20230210T033504_VV_E5B0-BURST
S1_043817_IW2_20230210T033503_VV_E5B0-BURST
S1_043817_IW1_20230210T033502_VV_E5B0-BURST
S1_043816_IW3_20230210T033502_VV_E5B0-BURST
S1_043816_IW2_20230210T033501_VV_E5B0-BURST
S1_043816_IW1_20230210T033500_VV_E5B0-BURST
S1_043815_IW3_20230210T033459_VV_E5B0-BURST
S1_043815_IW2_20230210T033458_VV_E5B0-BURST
S1_043815_IW1_20230210T033457_VV_E5B0-BURST
S1_043814_IW3_20230210T033456_VV_E5B0-BURST
S1_043814_IW2_20230210T033455_VV_E5B0-BURST
S1_043814_IW1_20230210T033454_VV_E5B0-BURST
S1_043813_IW3_20230210T033453_VV_E5B0-BURST
S1_043813_IW2_20230210T033452_VV_E5B0-BURST
S1_043813_IW1_20230210T033451_VV_E5B0-BURST
S1_043812_IW3_20230210T033451_VV_FAA6-BURST
S1_043812_IW2_20230210T033450_VV_FAA6-BURST
S1_043812_IW1_20230210T033449_VV_FAA6-BURST
S1_043811_IW3_20230210T033448_VV_FAA6-BURST
S1_043811_IW2_20230210T033447_VV_FAA6-BURST
S1_043811_IW1_20230210T033446_VV_FAA6-BURST
S1_043810_IW3_20230210T033445_VV_FAA6-BURST
S1_043810_IW2_20230210T033444_VV_FAA6-BURST
S1_043810_IW1_20230210T033443_VV_FAA6-BURST
S1_043809_IW3_20230210T033442_VV_FAA6-BURST
S1_043809_IW2_20230210T033441_VV_FAA6-BURST
S1_043809_IW1_20230210T033440_VV_FAA6-BURST
S1_043808_IW3_20230210T033439_VV_FAA6-BURST
S1_043808_IW2_20230210T033439_VV_FAA6-BURST
S1_043808_IW1_20230210T033438_VV_FAA6-BURST
S1_043807_IW3_20230210T033437_VV_FAA6-BURST
S1_043807_IW2_20230210T033436_VV_FAA6-BURST
S1_043807_IW1_20230210T033435_VV_FAA6-BURST
S1_043806_IW3_20230210T033434_VV_FAA6-BURST
S1_043806_IW2_20230210T033433_VV_FAA6-BURST
S1_043806_IW1_20230210T033432_VV_FAA6-BURST
S1_043805_IW3_20230210T033431_VV_FAA6-BURST
S1_043805_IW2_20230210T033430_VV_FAA6-BURST
S1_043805_IW1_20230210T033429_VV_FAA6-BURST
S1_043804_IW3_20230210T033428_VV_FAA6-BURST
S1_043804_IW2_20230210T033427_VV_FAA6-BURST
S1_043804_IW1_20230210T033427_VV_FAA6-BURST
S1_043803_IW3_20230210T033426_VV_FAA6-BURST
S1_043822_IW1_20230129T033517_VV_E089-BURST
S1_043821_IW3_20230129T033516_VV_BE0B-BURST
S1_043821_IW2_20230129T033515_VV_BE0B-BURST
S1_043821_IW1_20230129T033514_VV_BE0B-BURST
S1_043820_IW3_20230129T033513_VV_BE0B-BURST
S1_043820_IW2_20230129T033512_VV_BE0B-BURST
S1_043820_IW1_20230129T033512_VV_BE0B-BURST
S1_043819_IW3_20230129T033511_VV_BE0B-BURST
S1_043819_IW2_20230129T033510_VV_BE0B-BURST
S1_043819_IW1_20230129T033509_VV_BE0B-BURST
S1_043818_IW3_20230129T033508_VV_BE0B-BURST
S1_043818_IW2_20230129T033507_VV_BE0B-BURST
S1_043818_IW1_20230129T033506_VV_BE0B-BURST
S1_043817_IW3_20230129T033505_VV_BE0B-BURST
S1_043817_IW2_20230129T033504_VV_BE0B-BURST
S1_043817_IW1_20230129T033503_VV_BE0B-BURST
S1_043816_IW3_20230129T033502_VV_BE0B-BURST
S1_043816_IW2_20230129T033501_VV_BE0B-BURST
S1_043816_IW1_20230129T033501_VV_BE0B-BURST
S1_043815_IW3_20230129T033500_VV_BE0B-BURST
S1_043815_IW2_20230129T033459_VV_BE0B-BURST
S1_043815_IW1_20230129T033458_VV_BE0B-BURST
S1_043814_IW3_20230129T033457_VV_BE0B-BURST
S1_043814_IW2_20230129T033456_VV_BE0B-BURST
S1_043814_IW1_20230129T033455_VV_BE0B-BURST
S1_043813_IW3_20230129T033454_VV_BE0B-BURST
S1_043813_IW2_20230129T033453_VV_BE0B-BURST
S1_043813_IW1_20230129T033452_VV_BE0B-BURST
S1_043812_IW3_20230129T033451_VV_6FF2-BURST
S1_043812_IW2_20230129T033450_VV_6FF2-BURST
S1_043812_IW1_20230129T033449_VV_6FF2-BURST
S1_043811_IW3_20230129T033449_VV_6FF2-BURST
S1_043811_IW2_20230129T033448_VV_6FF2-BURST
S1_043811_IW1_20230129T033447_VV_6FF2-BURST
S1_043810_IW3_20230129T033446_VV_6FF2-BURST
S1_043810_IW2_20230129T033445_VV_6FF2-BURST
S1_043810_IW1_20230129T033444_VV_6FF2-BURST
S1_043809_IW3_20230129T033443_VV_6FF2-BURST
S1_043809_IW2_20230129T033442_VV_6FF2-BURST
S1_043809_IW1_20230129T033441_VV_6FF2-BURST
S1_043808_IW3_20230129T033440_VV_6FF2-BURST
S1_043808_IW2_20230129T033439_VV_6FF2-BURST
S1_043808_IW1_20230129T033438_VV_6FF2-BURST
S1_043807_IW3_20230129T033438_VV_6FF2-BURST
S1_043807_IW2_20230129T033437_VV_6FF2-BURST
S1_043807_IW1_20230129T033436_VV_6FF2-BURST
S1_043806_IW3_20230129T033435_VV_6FF2-BURST
S1_043806_IW2_20230129T033434_VV_6FF2-BURST
S1_043806_IW1_20230129T033433_VV_6FF2-BURST
S1_043805_IW3_20230129T033432_VV_6FF2-BURST
S1_043805_IW2_20230129T033431_VV_6FF2-BURST
S1_043805_IW1_20230129T033430_VV_6FF2-BURST
S1_043804_IW3_20230129T033429_VV_6FF2-BURST
S1_043804_IW2_20230129T033428_VV_6FF2-BURST
S1_043804_IW1_20230129T033427_VV_6FF2-BURST
S1_043803_IW3_20230129T033427_VV_6FF2-BURST
"""
BURSTS = list(filter(None, BURSTS.split('\n')))
print (f'Bursts defined: {len(BURSTS)}')

WORKDIR      = 'raw_kahr'
DATADIR      = 'data_kahr'
# output resolution defined as float value, meter
RESOLUTION   = 200.

# define DEM and landmask filenames inside data directory
DEM = f'{DATADIR}/dem.nc'
LANDMASK = f'{DATADIR}/landmask.nc'

# Magnitude Mw 7.8 & 7.5
# Region    CENTRAL TURKEY
# Date      2023-02-06
EPICENTERS = [37.24, 38.11,37.08, 37.17]
POI = gpd.GeoDataFrame(geometry=[shapely.geometry.Point(coord) for coord in np.reshape(EPICENTERS, (2,-1))])
POI

"""## Download and Unpack Datasets (Optional)

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

# Define AOI as the whole scenes extent.
AOI = S1.scan_slc(DATADIR)
# download Copernicus Global DEM 1 arc-second
Tiles().download_dem(AOI, filename=DEM).plot.imshow(cmap='cividis')

# download land mask 1 arc-second
Tiles().download_landmask(AOI, filename=LANDMASK).fillna(0).plot.imshow(cmap='binary_r')

"""## Run Local Dask Cluster

Launch Dask cluster for big data processing. Use "Dashboard" link below for the local cluster state and execution monitoring.
"""

# cleanup for repeatable runs
if 'client' in globals():
    client.close()
# tune to use 2 cores per worker
client = Client(n_workers=(psutil.cpu_count() // 2))
client

"""## Init SBAS

Search recursively for measurement (.tiff) and annotation (.xml) and orbit (.EOF) files in the DATA directory. It can be directory with full unzipped scenes (.SAFE) subdirectories or just a directory with the list of pairs of required .tiff and .xml files (maybe pre-filtered for orbit, polarization and subswath to save disk space). If orbit files and DEM are missed these will be downloaded automatically below.

### Select Original Secenes and Download DEM and Orbits Later

Use filters to find required subswath, polarization and orbit in original scenes .SAFE directories in the data directory.
"""

scenes = S1.scan_slc(DATADIR, polarization=POLARIZATION, orbit=ORBIT)

sbas = Stack(WORKDIR, drop_if_exists=True).set_scenes(scenes)
sbas.to_dataframe()

sbas.plot_scenes(POI=POI)

"""## Reframe Scenes (Optional)

Stitch sequential scenes and crop the subswath to a smaller area for faster processing when the full area is not needed.
"""

sbas.compute_reframe()

sbas.plot_scenes(POI=POI)

"""### Load DEM

The function below loads DEM from file or Xarray variable and converts heights to ellipsoidal model using EGM96 grid.
"""

# define the area of interest (AOI) to speedup the processing
sbas.load_dem(DEM, AOI)

sbas.plot_scenes(POI=POI)
plt.savefig('Estimated Scene Locations.jpg')

"""## Align Images"""

if 'google.colab' in sys.modules:
    # tune for Google Colab instances
    sbas.compute_align(n_jobs=(psutil.cpu_count() // 2))
else:
    sbas.compute_align()

"""## Geocoding Transform"""

sbas.compute_geocode(RESOLUTION)

sbas.plot_topo(POI=sbas.geocode(POI))
plt.savefig('Topography on WGS84 ellipsoid, [m].jpg')

"""## Interferogram"""

# for a pair of scenes only two interferograms can be produced
# this one is selected for scenes sorted by the date in direct order
pairs = [sbas.to_dataframe().index.unique()]
pairs

# load radar topography
topo = sbas.get_topo()
# load Sentinel-1 data
data = sbas.open_data()
# Gaussian filtering 400m cut-off wavelength with 4x16 multilooking on Sentinel-1 intensity
intensity = sbas.multilooking(np.square(np.abs(data)), wavelength=400, coarsen=(4,16))
# calculate phase difference with topography correction
phase = sbas.phasediff(pairs, data, topo)
# Gaussian filtering 400m cut-off wavelength with 4x16 multilooking
phase = sbas.multilooking(phase, wavelength=400, coarsen=(4,16))
# correlation with 1:4 range decimation to about 15m resolution
corr = sbas.correlation(phase, intensity)
# Goldstein filter in 32 pixel patch size on square grid cells produced using multilooking
phase_goldstein = sbas.goldstein(phase, corr, 32)
# convert complex phase difference to interferogram
intf = sbas.interferogram(phase_goldstein)
# decimate the 1:4 multilooking grids to specified resolution
decimator = sbas.decimator(resolution=RESOLUTION, grid=intf)
# compute together because correlation depends on phase, and filtered phase depends on correlation.
tqdm_dask(result := dask.persist(decimator(corr), decimator(intf)), desc='Compute Phase and Correlation')
# unpack results for a single interferogram
corr, intf = [grid[0] for grid in result]
intf

# geocode to geographic coordinates and crop empty borders
intf_ll = sbas.ra2ll(intf)
corr_ll = sbas.ra2ll(corr)

sbas.plot_interferogram(intf_ll, caption='Phase\nGeographic Coordinates, [rad]', POI=POI)
plt.savefig('Phase Geographic Coordinates, [rad].jpg')

sbas.plot_correlation(corr_ll, caption='Correlation\nGeographic Coordinates', POI=POI)
plt.savefig('Correlation Geographic Coordinates, [rad].jpg')

"""## Landmask

Interferogram presents just a noise for water surfaces and unwrapping is meaningless long for these areas. Landmask allows to exclude water sufraces to produce better looking unwrapping results and much faster. Landmask in geographic coordinates is suitable to check it on the map while for unwrapping required landmask in radar coordinates.
"""

sbas.load_landmask(LANDMASK)

landmask_ll = sbas.get_landmask().reindex_like(intf_ll, method='nearest')
landmask = sbas.ll2ra(landmask_ll).reindex_like(intf, method='nearest')

sbas.plot_landmask(landmask=landmask_ll, caption='Landmask\nGeographic Coordinates', POI=POI)
plt.savefig('Landmask Geographic Coordinates, [rad].jpg')

sbas.plot_interferogram(intf_ll.where(landmask_ll), caption='Landmasked Phase\nGeographic Coordinates, [rad]', POI=POI)
plt.savefig('Landmasked Phase Geographic Coordinates, [rad].jpg')

sbas.export_vtk(intf[::3,::3], 'intf', mask='auto')

# build interactive 3D plot
plotter = pv.Plotter(notebook=True)
plotter.add_mesh(pv.read('intf.vtk').scale([1, 1, 0.00002], inplace=True), scalars='phase', cmap='turbo', ambient=0.1, show_scalar_bar=True)
plotter.show_axes()
plotter.show(screenshot='3D Interferogram.png', jupyter_backend='panel', return_viewer=True)
plotter.add_title(f'Interactive Interferogram on DEM', font_size=32)
plotter._on_first_render_request()
panel.panel(
    plotter.render_window, orientation_widget=plotter.renderer.axes_enabled,
    enable_keybindings=False, sizing_mode='stretch_width', min_height=600
)

"""## Unwrapping

Unwrapping process requires a lot of RAM and that's really RAM consuming when a lot of parallel proccesses running togeter. To limit the parallel processing tasks apply argument "n_jobs". The default value n_jobs=-1 means all the processor cores van be used. Also, use interferogram decimation above to produce smaller interferograms. And in addition a custom SNAPHU configuration can reduce RAM usage as explained below.

### Generate Custom SNAPHU Config

Default SNAPHU configuration allows to run multiple unwrapping tasks in parallel. At the same time, for a single interferogram processing or large interferograms unwrapping SNAPHU tiling can decrease the both processing time and RAM comsumption. Be careful to prevent unconnected zones on the tiles when a high coherency area is fully arounded by low-coherent buffer on some tiles (redefine tiles or increase tiles row and column overlapping parameters ROWOVRLP and COLOVRLP).
"""

# small tiles unwrapping is faster but some details can be missed
conf = sbas.snaphu_config(defomax=None,
                          NTILEROW=2,
                          NTILECOL=2,
                          ROWOVRLP=100, COLOVRLP=100)
# check the generated SNAPHU config and tune the SNAPHU parameters above if needed.
print ('SNAPHU custom config generated:')
print (conf)

"""### Interferogram Unwrapping

SNAPHU unwrapper allows to split large scene to tiles for parallel processing and accurately enough merge the tiles to a single image. That's especially helpful to unwrap a single interferogram using all the processor cores and save RAM consumption drastically.
"""

# Low-coherence phases can be masked using a threshold value. Offshore areas in the phase are masked.
# The masked phase is internally interpolated using the phases of the nearest pixels with good coherence.
# Pixels located far from well-coherent regions are set to zero phase during the unwrapping processing.
tqdm_dask(unwrap := sbas.unwrap_snaphu(intf.where(landmask), corr, conf=conf).persist(), desc='SNAPHU Unwrapping')

# geocode to geographic coordinates and crop empty borders
unwrap_ll = sbas.ra2ll(unwrap.phase)

sbas.plot_phase(unwrap_ll, caption='Unwrapped Phase\nGeographic Coordinates, [rad]', quantile=[0.01, 0.99], POI=POI)
plt.savefig('Unwrapped Phase Geographic Coordinates, [rad].jpg')

"""## Detrend"""

tqdm_dask(detrend := (unwrap.phase - sbas.gaussian(unwrap.phase, wavelength=300000)).persist(),
          desc='Detrending')

detrend_ll = sbas.ra2ll(detrend)

sbas.plot_phase(detrend_ll, caption='Detrended Unwrapped Phase\nGeographic Coordinates, [rad]', quantile=[0.01, 0.99], POI=POI)
plt.savefig('Detrended Unwrapped Phase Geographic Coordinates, [rad].jpg')

"""## LOS Displacement"""

# geocode to geographic coordinates
los_disp_mm_ll = sbas.ra2ll(sbas.los_displacement_mm(detrend))

sbas.plot_displacement(los_disp_mm_ll, caption='Detrended LOS Displacement\nGeographic Coordinates, [mm]', quantile=[0.01, 0.99], POI=POI)
plt.savefig('Detrended LOS Displacement Geographic Coordinates, [rad].jpg')

sbas.export_vtk(los_disp_mm_ll[::3,::3], 'los', mask='auto')

# build interactive 3D plot
plotter = pv.Plotter(notebook=True)
plotter.add_mesh(pv.read('los.vtk').scale([1, 1, 0.00002], inplace=True), scalars='los', cmap='turbo', ambient=0.1, show_scalar_bar=True)
plotter.show_axes()
plotter.show(screenshot='3D LOS Displacement.png', jupyter_backend='panel', return_viewer=True)
plotter.add_title(f'Interactive LOS Displacement on DEM', font_size=32)
plotter._on_first_render_request()
panel.panel(
    plotter.render_window, orientation_widget=plotter.renderer.axes_enabled,
    enable_keybindings=False, sizing_mode='stretch_width', min_height=600
)

"""## Vertical and East-West Displacements Projections

LOS displacement projections as vertical and east-west displacements can be calculated using incidence angle defined on the grid.
"""

incidence_angle = sbas.incidence_angle()

sbas.plot_incidence_angle(POI=sbas.geocode(POI))
plt.savefig('Incidence Angle Radar Coordinates, [rad].jpg')

vert_disp_mm_ll = sbas.ra2ll(sbas.vertical_displacement_mm(detrend))
east_disp_mm_ll = sbas.ra2ll(sbas.eastwest_displacement_mm(detrend))

sbas.plot_displacement(vert_disp_mm_ll, caption='Vertical Projection LOS Displacement\nGeographic Coordinates, [mm]', quantile=[0.01, 0.99], POI=POI)
plt.savefig('Vertical Projection LOS Displacement Geographic Coordinates, [mm].jpg')

sbas.plot_displacement(east_disp_mm_ll, caption='East-West Projection LOS Displacement\nGeographic Coordinates, [mm]', quantile=[0.01, 0.99], POI=POI)
plt.savefig('East-West Projection LOS Displacement Geographic Coordinates, [mm].jpg')

sbas.export_vtk(vert_disp_mm_ll.rename('vdisp')[::3,::3], 'vdisp', mask='auto')

# build interactive 3D plot
plotter = pv.Plotter(notebook=True)
plotter.add_mesh(pv.read('vdisp.vtk').scale([1, 1, 0.00002], inplace=True), scalars='vdisp', cmap='turbo', ambient=0.1, show_scalar_bar=True)
plotter.show_axes()
plotter.show(screenshot='3D Vertical Displacement.png', jupyter_backend='panel', return_viewer=True)
plotter.add_title(f'Interactive Vertical Displacement on DEM', font_size=32)
plotter._on_first_render_request()
panel.panel(
    plotter.render_window, orientation_widget=plotter.renderer.axes_enabled,
    enable_keybindings=False, sizing_mode='stretch_width', min_height=600
)

sbas.export_vtk(east_disp_mm_ll.rename('edisp')[::3,::3], 'edisp', mask='auto')

# build interactive 3D plot
plotter = pv.Plotter(notebook=True)
plotter.add_mesh(pv.read('edisp.vtk').scale([1, 1, 0.00002], inplace=True), scalars='edisp', cmap='turbo', ambient=0.1, show_scalar_bar=True)
plotter.show_axes()
plotter.show(screenshot='3D East-West Displacement.png', jupyter_backend='panel', return_viewer=True)
plotter.add_title(f'Interactive East-West Displacement on DEM', font_size=32)
plotter._on_first_render_request()
panel.panel(
    plotter.render_window, orientation_widget=plotter.renderer.axes_enabled,
    enable_keybindings=False, sizing_mode='stretch_width', min_height=600
)

"""## Save Geographic Coordinates NetCDF Grids"""

filename = 'corr.nc'
# drop the existing file first
!rm -fr {filename}
# apply landmask before and geocode
delayed = sbas.ra2ll(corr.where(landmask)).to_netcdf(filename, engine=sbas.netcdf_engine, compute=False)
tqdm_dask(dask.persist(delayed), desc='Saving NetCDF')

filename = 'intf.nc'
# drop the existing file first
!rm -fr {filename}
# apply landmask before and geocode
delayed = sbas.ra2ll(intf.where(landmask)).to_netcdf(filename, engine=sbas.netcdf_engine, compute=False)
tqdm_dask(dask.persist(delayed), desc='Saving NetCDF')

"""## Download Geographic Coordinates NetCDF Grids from Google Colab"""

if 'google.colab' in sys.modules:
    from google.colab import files
    files.download('corr.nc')
    files.download('intf.nc')