# ----------------------------------------------------------------------------
# PyGMTSAR
# 
# This file is part of the PyGMTSAR project: https://github.com/mobigroup/gmtsar
# 
# Copyright (c) 2024, Alexey Pechnikov
# 
# Licensed under the BSD 3-Clause License (see LICENSE for details)
# ----------------------------------------------------------------------------
from .datagrid import datagrid
from .tqdm_joblib import tqdm_joblib

class GMT(datagrid, tqdm_joblib):
    
    # https://docs.generic-mapping-tools.org/6.0/datasets/earth_relief.html
    # only bicubic interpolation supported as the best one for the case
    def download_dem(self, geometry, filename=None, product='1s', skip_exist=True):
        """
        Download and preprocess SRTM digital elevation model (DEM) data using GMT library.

        Parameters
        ----------
        product : str, optional
            Product type of the DEM data. Available options are '1s' or 'SRTM1' (1 arcsec ~= 30m, default)
            and '3s' or 'SRTM3' (3 arcsec ~= 90m).

        Returns
        -------
        None or Xarray Dataarray

        Examples
        --------
        Download default STRM1 DEM (~30 meters):
        GMT.download_dem()

        Download STRM3 DEM (~90 meters):
        GMT.download_dem(product='STRM3')
        
        Download default STRM DEM to cover the selected area AOI:
        GMT.download_dem(AOI)
        
        Download default STRM DEM to cover all the scenes:
        GMT.download_dem(stack.get_extent().buffer(stack.buffer_degrees))

        import pygmt
        # Set the GMT data server limit to N Mb to allow for remote downloads
        pygmt.config(GMT_DATA_SERVER_LIMIT=1e6)
        GMT.download_dem(AOI, product='1s')

        Notes
        -----
        This method uses the GMT servers to download SRTM 1 or 3 arc-second DEM data. The downloaded data is then
        preprocessed by removing the EGM96 geoid to make the heights relative to the WGS84 ellipsoid.
        """
        import numpy as np
        import pygmt
        # suppress warnings
        pygmt.config(GMT_VERBOSE='errors')
        import os
        from tqdm.auto import tqdm

        if product in ['SRTM1', '1s', '01s']:
            resolution = '01s'
        elif product in ['SRTM3', '3s', '03s']:
            resolution = '03s'
        else:
            print (f'ERROR: unknown product {product}. Available only SRTM1 ("01s") and SRTM3 ("03s") DEM using GMT servers')
            return

        if filename is not None and os.path.exists(filename) and skip_exist:
            print ('NOTE: DEM file exists, ignore the command. Use "skip_exist=False" or omit the filename to allow new downloading')
            return

        lon_start, lat_start, lon_end, lat_end = self.get_bounds(geometry)
        with tqdm(desc='GMT SRTM DEM Downloading', total=1) as pbar:
            # download DEM using GMT extent W E S N
            ortho = pygmt.datasets.load_earth_relief(resolution=resolution, region=[lon_start, lon_end, lat_start, lat_end])
            # heights correction
            geoid = self.get_geoid(ortho)
            dem = (ortho + geoid).rename('dem')
            pbar.update(1)

        if filename is not None:
            if os.path.exists(filename):
                os.remove(filename)
            encoding = {'dem': self._compression(dem.shape)}
            dem.to_netcdf(filename, encoding=encoding, engine=self.netcdf_engine)
        else:
            return dem

    def download_landmask(self, geometry, filename=None, product='1s', skip_exist=True):
        """
        Download the landmask and save as NetCDF file.

        Parameters
        ----------
        product : str, optional
                Available options are '1s' (1 arcsec ~= 30m, default) and '3s' (3 arcsec ~= 90m).

        Examples
        --------
        from pygmtsar import GMT
        landmask = GMT().download_landmask(stack.get_dem())

        Notes
        -----
        This method downloads the landmask using GMT's local data or server.
        """
        import geopandas as gpd
        import numpy as np
        import pygmt
        # suppress warnings
        pygmt.config(GMT_VERBOSE='errors')
        import os
        #import subprocess
        from tqdm.auto import tqdm

        if filename is not None and os.path.exists(filename) and skip_exist:
            print ('NOTE: landmask file exists, ignore the command. Use "skip_exist=False" or omit the filename to allow new downloading')
            return

        if not product in ['1s', '3s']:
            print (f'ERROR: unknown product {product}. Available only "1s" or "3s" land mask using GMT servers')
            return

        lon_start, lat_start, lon_end, lat_end = self.get_bounds(geometry)
        with tqdm(desc='GMT Landmask Downloading', total=1) as pbar:
            landmask = pygmt.grdlandmask(resolution='f', region=[lon_start, lon_end, lat_start, lat_end], spacing=product, maskvalues='NaN/1')
            pbar.update(1)

        if filename is not None:
            if os.path.exists(filename):
                os.remove(filename)
            encoding = {'landmask': self._compression(landmask.shape)}
            landmask.to_netcdf(filename, encoding=encoding, engine=self.netcdf_engine)
        else:
            return landmask