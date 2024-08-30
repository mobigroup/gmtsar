# -*- coding: utf-8 -*-
"""Türkiye_Elevation_2019.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19PLuebOZ4gaYX5ym1H7SwUbJKfl23qPr

## PyGMTSAR Elevation Map

This area elevation map is processed in the ESA tutorial available at: http://step.esa.int/docs/tutorials/S1TBX%20DEM%20generation%20with%20Sentinel-1%20IW%20Tutorial.pdf

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

"""## Define 3 Sentinel-1 SLC Scenes and Processing Parameters

When you need more scenes and SBAS analysis  see examples on PyGMTSAR GitHub page https://github.com/mobigroup/gmtsar

### Descending Orbit Configuration
"""

SCENES = ['S1B_IW_SLC__1SDV_20190702T032447_20190702T032514_016949_01FE47_69C5',
          'S1A_IW_SLC__1SDV_20190708T032532_20190708T032559_028020_032A14_33CA']
ORBIT        = 'D'
SUBSWATH     = 2

WORKDIR      = 'raw_dem'
DATADIR      = 'data_dem'
POLARIZATION = 'VV'

# define DEM and landmask filenames inside data directory
DEM = f'{DATADIR}/dem.nc'

geojson = '''
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[39.5, 40], [40, 39.5]]
  },
  "properties": {}
}
'''
POI = gpd.GeoDataFrame.from_features([json.loads(geojson)])

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
print(asf.download(DATADIR, SCENES, SUBSWATH))

# scan the data directory for SLC scenes and download missed orbits
S1.download_orbits(DATADIR, S1.scan_slc(DATADIR))

# Define AOI as the whole scenes extent.
AOI = S1.scan_slc(DATADIR)
# download Copernicus Global DEM 1 arc-second
Tiles().download_dem(AOI, filename=DEM).plot.imshow(cmap='cividis')

"""## Run Local Dask Cluster

Launch Dask cluster for local and distributed multicore computing. That's possible to process terabyte scale Sentinel-1 SLC datasets on Apple Air 16 GB RAM.
"""

# simple Dask initialization
if 'client' in globals():
    client.close()
client = Client()
client

"""## Init SBAS

Search recursively for measurement (.tiff) and annotation (.xml) and orbit (.EOF) files in the DATA directory. It can be directory with full unzipped scenes (.SAFE) subdirectories or just a directory with the list of pairs of required .tiff and .xml files (maybe pre-filtered for orbit, polarization and subswath to save disk space). If orbit files and DEM are missed these will be downloaded automatically below.

### Select Original Secenes and Download DEM and Orbits Later

Use filters to find required subswath, polarization and orbit in original scenes .SAFE directories in the data directory.
"""

scenes = S1.scan_slc(DATADIR, subswath=SUBSWATH, polarization=POLARIZATION)

sbas = Stack(WORKDIR, drop_if_exists=True).set_scenes(scenes)
sbas.to_dataframe()

sbas.plot_scenes(AOI=POI)

"""## Reframe Scenes (Optional)

Stitch sequential scenes and crop the subswath to a smaller area for faster processing when the full area is not needed.
"""

sbas.compute_reframe(POI)

sbas.plot_scenes(AOI=POI)

"""### Load DEM

The function below loads DEM from file or Xarray variable and converts heights to ellipsoidal model using EGM96 grid.
"""

# define the area of interest (AOI) to speedup the processing
sbas.load_dem(DEM, AOI)

sbas.plot_scenes(AOI=POI)
plt.savefig('Estimated Scene Locations.jpg')

"""## Align Images"""

sbas.compute_align()

"""## Geocoding Transform"""

# geocode multilooking grid 1x4 (~15m)
sbas.compute_geocode((1,4))

sbas.plot_topo()
plt.savefig('Topography on WGS84 ellipsoid, [m].jpg')

"""## Baseline"""

# note: ref-rep dates order inverted in the referenced paper, do the same
baseline_pairs = sbas.sbas_pairs(invert=True)
baseline_pairs

"""## Interferogram

The code below is detailed for education reasons and can be more compact excluding optional arguments. See other PyGMTSAR examples for shorter version.
"""

# load Sentinel-1 data and crop a subset
data = sbas.open_data().sel(y=slice(50, 2750), x=slice(1000,25000))
# Gaussian filtering 200m cut-off wavelength with multilooking 1x4 on Sentinel-1 intensity
intensity15m = sbas.multilooking(np.square(np.abs(data)), wavelength=100, coarsen=(1,4))
# calculate phase difference without topography correction and with flat-earth correction
phase = sbas.phasediff(baseline_pairs, data, topo=0)
# Gaussian filtering 400m cut-off wavelength with 1:4 range multilooking
phase15m = sbas.multilooking(phase, wavelength=100, coarsen=(1,4))
# correlation with 1:4 range decimation to about 15m resolution
corr15m = sbas.correlation(phase15m, intensity15m)
# Goldstein filter in 32 pixel patch size on square grid cells produced using 1:4 range multilooking
phase15m_goldstein = sbas.goldstein(phase15m, corr15m, 32)
# convert complex phase difference to interferogram
intf15m = sbas.interferogram(phase15m_goldstein)
# compute together because correlation depends on phase, and filtered phase depends on correlation.
tqdm_dask(result := dask.persist(corr15m, intf15m), desc='Compute Phase and Correlation')
# unpack results for a single interferogram
corr, intf = [grid[0] for grid in result]

sbas.plot_interferogram(intf)
plt.savefig('Phase, [rad].jpg')

sbas.plot_correlation(corr)
plt.savefig('Correlation.jpg')

sbas.export_vtk(intf[::8,::8], 'intf', mask='auto')

# build interactive 3D plot
plotter = pv.Plotter(notebook=True)
plotter.add_mesh(pv.read('intf.vtk').scale([1, 1, 0.00005], inplace=True), scalars='phase', cmap='turbo', ambient=0.1, show_scalar_bar=True)
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

Attention: in case of crash on MacOS Apple Silicon run Jupyter as

`OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES no_proxy='*' jupyter notebook`
"""

# mask low-coherence areas using threshold value 0.1
tqdm_dask(unwrap := sbas.unwrap_snaphu(intf, corr.where(corr>=0.1)).persist(), desc='SNAPHU Unwrapping')

sbas.plot_phase(unwrap.phase, caption='Phase, [rad]', quantile=[0.01, 0.99])

"""## Phase to Elevation"""

baseline = baseline_pairs.loc[0,'baseline']
baseline

# for reference, compute height for a single fringe
sbas.elevation_m(2*np.pi*xr.ones_like(unwrap.phase), baseline).mean().compute()

ele = sbas.elevation_m(unwrap.phase, baseline)

points_topo = sbas.get_topo().reindex_like(unwrap, method='nearest').values.ravel()
points_ele = ele.values.ravel()
nanmask = np.isnan(points_topo) | np.isnan(points_ele)
points_topo = points_topo[~nanmask]
points_ele = points_ele[~nanmask]

points_topo = points_topo - points_topo.mean()
points_ele = points_ele - points_ele.mean()

plt.figure(figsize=(12, 4), dpi=300)
plt.scatter(points_ele, points_topo, c='y', alpha=0.01, s=0.01)

# adding a 1:1 line
max_value = max(points_topo.max(), points_ele.max())
min_value = min(points_topo.min(), points_ele.min())
plt.plot([min_value, max_value], [min_value, max_value], 'k--')

plt.xlabel('Elevation, m', fontsize=16)
plt.ylabel('DEM, m', fontsize=16)
plt.title('Cross-Comparison between Sentinel-1 Elevation and Copernicus GLO-30 DEM', fontsize=18)
plt.grid(True)
plt.show()

sbas.export_vtk(sbas.get_dem()[::10,::10], 'dem', mask='auto')
sbas.export_vtk(ele[::8,::8], 'ele', mask='auto')

plotter = pv.Plotter(shape=(1, 2), notebook=True)

plotter.subplot(0, 0)
plotter.add_mesh(pv.read('ele.vtk').scale([1, 1, 0.00002], inplace=True), scalars='ele', cmap='turbo', ambient=0.1, show_scalar_bar=True)
plotter.add_title(f'Interactive Sentinel-1 Elevation Map', font_size=32)

plotter.subplot(0, 1)
plotter.add_mesh(pv.read('dem.vtk').scale([1, 1, 0.00002], inplace=True), scalars='dem', cmap='turbo', ambient=0.1, show_scalar_bar=True)
plotter.add_title(f'Interactive GLO-30 DEM', font_size=32)

plotter.show_axes()
plotter.show(screenshot='3D LOS Displacements Grid.png', jupyter_backend='panel', return_viewer=True)
plotter._on_first_render_request()
panel.panel(
    plotter.render_window, orientation_widget=plotter.renderer.axes_enabled,
    enable_keybindings=False, sizing_mode='stretch_width', min_height=600
)

"""## Save the Results

Save the results in geospatial data formats like to NetCDF, GeoTIFF and others. The both formats (NetCDF and GeoTIFF) can be opened in QGIS and other GIS applications.
"""

# save the results
# geocode to geographic coordinates and crop empty borders
sbas.cropna(sbas.ra2ll(ele)).load().to_netcdf('elevation.nc', engine=sbas.netcdf_engine)

"""## Export from Google Colab"""

if 'google.colab' in sys.modules:
    from google.colab import files
    files.download('elevation.nc')
    files.download('ele.vtk')