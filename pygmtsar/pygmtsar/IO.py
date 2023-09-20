# ----------------------------------------------------------------------------
# PyGMTSAR
#.
# This file is part of the PyGMTSAR project: https://github.com/mobigroup/gmtsar
#.
# Copyright (c) 2023, Alexey Pechnikov
#.
# Licensed under the BSD 3-Clause License (see LICENSE for details)
# ----------------------------------------------------------------------------
from .datagrid import datagrid
from pygmtsar import tqdm_dask

class IO(datagrid):

    # processing directory
    basedir = '.'

    def dump(self, to_path=None):
        """
        Dump Stack object state to a pickle file (Stack.pickle in the processing directory by default).

        Parameters
        ----------
        to_path : str, optional
            Path to the output dump file. If not provided, the default dump file in the processing directory is used.

        Returns
        -------
        None

        Examples
        --------
        Dump the current state to the default dump file in the processing directory:
        stack.dump()

        Notes
        -----
        This method serializes the state of the Stack object and saves it to a pickle file. The pickle file can be used to
        restore the Stack object with its processed data and configuration. By default, the dump file is named "Stack.pickle"
        and is saved in the processing directory. An alternative file path can be provided using the `to_path` parameter.
        """
        import pickle
        import os

        if to_path is None:
            stack_pickle = os.path.join(self.basedir, 'Stack.pickle')
        else:
            if os.path.isdir(to_path):
                stack_pickle = os.path.join(to_path, 'Stack.pickle')
            else:
                stack_pickle = to_path
    
        print (f'NOTE: save state to file {stack_pickle}')
        pickle.dump(self, open(stack_pickle, 'wb'))

        return

    @staticmethod
    def restore(from_path):
        """
        Restore Stack object state from a pickle file (Stack.pickle in the processing directory by default).

        Parameters
        ----------
        from_path : str
            Path to the input dump file.

        Returns
        -------
        Stack
            The restored Stack object.

        Examples
        --------
        Restore the current state from the default dump file in the processing directory:
        Stack.restore()

        Notes
        -----
        This static method restores the state of an Stack object from a pickle file. The pickle file should contain the
        serialized state of the Stack object, including its processed data and configuration. By default, the method assumes
        the input file is named "Stack.pickle" and is located in the processing directory. An alternative file path can be
        provided using the `from_path` parameter. The method returns the restored Stack object.
        """
        import pickle
        import os

        if os.path.isdir(from_path):
            stack_pickle = os.path.join(from_path, 'Stack.pickle')
        else:
            stack_pickle = from_path

        print (f'NOTE: load state from file {stack_pickle}')
        return pickle.load(open(stack_pickle, 'rb'))


    def backup(self, backup_dir, copy=False, debug=False):
        """
        Backup framed Stack scenes, orbits, DEM, and landmask files to build a minimal reproducible dataset.

        Parameters
        ----------
        backup_dir : str
            The backup directory where the files will be copied.
        copy : bool, optional
            Flag indicating whether to make a copy of scene and orbit files and remove the originals in the work directory.
            If False, the files will be moved to the backup directory. Default is False.
        debug : bool, optional
            Flag indicating whether to print debug information. Default is False.

        Returns
        -------
        None

        Examples
        --------
        Backup the files to the specified directory:
        stack.backup('backup')

        Open the backup for the reproducible run by defining it as a new data directory:
        stack = Stack('backup', 'backup/DEM_WGS84.nc', 'raw')

        Notes
        -----
        This method backs up the framed Stack scenes, orbits, DEM, and landmask files to a specified backup directory.
        It provides a way to create a minimal reproducible dataset by preserving the necessary files for processing.
        The method creates the backup directory if it does not exist. By default, the method moves the scene and orbit files
        to the backup directory, effectively removing them from the work directory. The DEM and landmask files are always
        copied to the backup directory. If the `copy` parameter is set to True, the scene and orbit files will be copied
        instead of moved. Use caution when setting `copy` to True as it can result in duplicated files and consume
        additional storage space. The method also updates the Stack object's dataframe to mark the removed files as empty.
        """
        import os
        import shutil

        os.makedirs(backup_dir, exist_ok=True)

        # this optional file is dumped state, copy it if exists
        # auto-generated file can't be a symlink but user-defined symlink target should be copied
        filename = os.path.join(self.basedir, 'Stack.pickle')
        if os.path.exists(filename):
            if debug:
                print ('DEBUG: copy', filename, backup_dir)
            shutil.copy2(filename, backup_dir, follow_symlinks=True)

        # these files required to continue the processing, do not remove and copy only
        filenames = [self.dem_filename, self.landmask_filename]
        for filename in filenames:
            # DEM and landmask can be not defined
            if filename is None:
                continue
            if debug:
                print ('DEBUG: copy', filename, backup_dir)
            shutil.copy2(filename, backup_dir, follow_symlinks=True)

        # these files are large and are not required to continue the processing
        filenames = []
        for record in self.df.itertuples():
            for filename in [record.datapath, record.metapath, record.orbitpath]:
                filenames += filename if isinstance(filename, list) else [filename]
        for filename in filenames:
            # orbit files can be not defined
            if filename is None:
                continue
            # copy and delete the original later to prevent cross-device links issues
            if debug:
                print ('DEBUG: copy', filename, backup_dir)
            shutil.copy2(filename, backup_dir, follow_symlinks=True)
            if not copy and self.basedir == os.path.dirname(filename):
                # when copy is not needed then delete files in work directory only
                if debug:
                    print ('DEBUG: remove', filename)
                os.remove(filename)

        if not copy:
            # mark as empty all the removed files
            for col in ['datapath','metapath','orbitpath']:
                self.df[col] = None
        return

    def get_filename(self, name, add_subswath=True):
        import os

        if add_subswath:
            subswath = self.get_subswath()
            prefix = f'F{subswath}_'
        else:
            prefix = ''

        filename = os.path.join(self.basedir, f'{prefix}{name}.grd')
        return filename

    def get_filenames(self, pairs, name, add_subswath=True):
        """
        Get the filenames of the data grids. The filenames are determined by the subswath, pairs, and name parameters.

        Parameters
        ----------
        subswath : int or None
            The subswath number. If None, the function will determine it based on the dataset.
        pairs : np.ndarray or pd.DataFrame or None
            An array or DataFrame of pairs. If None, the function will open a single grid or a set of subswath grids.
        name : str
            The name of the grid to be opened.
        add_subswath : bool, optional
            Whether to add subswath to the prefix of the filename. Default is True.

        Returns
        -------
        str or list of str
            The filename or a list of filenames of the grids.
        """
        import pandas as pd
        import numpy as np
        import os

        if add_subswath:
            subswath = self.get_subswath()
            prefix = f'F{subswath}_'
        else:
            prefix = ''

        if isinstance(pairs, pd.DataFrame):
            # convert to standalone DataFrame first
            pairs = self.get_pairs(pairs)[['ref', 'rep']].astype(str).values
        else:
            pairs = np.asarray(pairs)

        filenames = []
        if len(pairs.shape) == 1:
            # read all the grids from files
            for date in sorted(pairs):
                filename = os.path.join(self.basedir, f'{prefix}{name}_{date}.grd'.replace('-',''))
                filenames.append(filename)
        elif len(pairs.shape) == 2:
            # read all the grids from files
            for pair in pairs:
                filename = os.path.join(self.basedir, f'{prefix}{pair[0]}_{pair[1]}_{name}.grd'.replace('-',''))
                filenames.append(filename)
        return filenames

    def load_pairs(self, name='phase'):
        import numpy as np
        from glob import glob

        # find all the named grids
        pattern = self.get_filename(f'????????_????????_{name}')

        filenames = glob(pattern, recursive=False)
        pairs = [filename.split('_')[-3:-1] for filename in sorted(filenames)]
        # return as numpy array for compatibility reasons
        return np.asarray(pairs)

    def open_grid(self, name, add_subswath=True, chunksize=None):
        """
        stack.open_grid('intf_ll2ra')
        stack.open_grid('intf_ra2ll')
        stack.open_grid('intfweight')
        """
        import xarray as xr

        if chunksize is None:
            chunksize = self.chunksize

        filename = self.get_filename(name, add_subswath=add_subswath)
        ds = xr.open_dataset(filename, engine=self.engine, chunks=chunksize)
        if 'a' in ds.dims and 'r' in ds.dims:
            ds = ds.rename({'a': 'y', 'r': 'x'})
        if len(ds.data_vars) == 1:
            return ds[list(ds.data_vars)[0]]
        return ds

    def save_grid(self, data, name, caption='Saving 2D grid', chunksize=None):
        import xarray as xr
        import dask
        import os

        if chunksize is None:
            chunksize = self.chunksize

        # save to NetCDF file
        filename = self.get_filename(name)
        if os.path.exists(filename):
            os.remove(filename)

        if isinstance(data, xr.Dataset):
            encoding = {varname: self.compression(data[varname].shape, chunksize=chunksize) for varname in data.data_vars}
        elif isinstance(data, xr.DataArray):
            encoding = {data.name: self.compression(data.shape, chunksize=chunksize)}
        else:
            raise Exception('Argument grid is not xr.Dataset or xr.DataArray object')
        delayed = data.to_netcdf(filename,
                              encoding=encoding,
                              engine=self.engine,
                              compute=False)

        tqdm_dask(dask.persist(delayed), desc=caption)
        # cleanup - sometimes writing NetCDF handlers are not closed immediately and block reading access
        import gc; gc.collect()

    def open_pairs(self, pairs, name, add_subswath=True, chunksize=None):
        """
        stack.open_pairs(baseline_pairs,'phasefilt')
        """
        import xarray as xr
        import pandas as pd
        import numpy as np
        import os

        if chunksize is None:
            chunksize = self.chunksize
    
        # convert to 2D single-element array
        pairs = self.get_pairs(pairs)[['ref','rep']].astype(str).values

        filenames = self.get_filenames(pairs, name, add_subswath=add_subswath)
        #print ('filenames', filenames)
        #print ('keys', keys)

        ds = xr.open_mfdataset(
            filenames,
            engine=self.engine,
            chunks=chunksize,
            parallel=True,
            concat_dim='pair',
            combine='nested'
        ).assign(pair=[' '.join(pair) for pair in pairs])
    
        ds.coords['ref'] = xr.DataArray(pd.to_datetime(pairs[:,0]), coords=ds.pair.coords)
        ds.coords['rep'] = xr.DataArray(pd.to_datetime(pairs[:,1]), coords=ds.pair.coords)

        if 'a' in ds.dims and 'r' in ds.dims:
            ds = ds.rename({'a': 'y', 'r': 'x'})

        if len(ds.data_vars) == 1:
            return ds[list(ds.data_vars)[0]].rename(name)
        return ds

    def open_stack(self, dates=None, intensity=False, scale=2.5e-07, chunksize=None):
        import xarray as xr
        import pandas as pd
        import numpy as np
        import dask

        if chunksize is None:
            chunksize = self.chunksize

        if dates is None:
            dates = self.df.index.values
        #print ('dates', dates)
        # select radar coordinates extent
        rng_max = self.PRM().get('num_rng_bins')
        #print ('azi_max', azi_max, 'rng_max', rng_max)
        # use SLC-related chunks for faster processing
        minichunksize = int(np.round(chunksize**2/rng_max))
        #print (minichunksize)
        slcs = [self.PRM(date).read_SLC_int(intensity=intensity, scale=scale, chunksize=minichunksize) for date in dates]
        # build stack
        slcs = xr.concat(slcs, dim='date')
        slcs['date'] = pd.to_datetime(dates)
        return slcs
# 
#     def open_stack_geotif(self, dates=None, subswath=None, intensity=False, chunksize=None):
#         """
#         tiffs = stack.open_stack_geotif(['2022-06-16', '2022-06-28'], intensity=True)
#         """
#         import xarray as xr
#         import rioxarray as rio
#         import pandas as pd
#         import numpy as np
#         # from GMTSAR code
#         DFACT = 2.5e-07
#     
#         if chunksize is None:
#             chunksize = self.chunksize
# 
#         if subswath is None:
#             subswaths = self.get_subswaths()
#         else:
#             subswaths = [subswath]
# 
#         stack = []
#         for swath in self.get_subswaths():
#             if dates is None:
#                 dates = self.df[self.df['subswath']==swath].index.values
#             #print ('dates', dates)
#             tiffs = self.df[(self.df['subswath']==swath)&(self.df.index.isin(dates))].datapath.values
#             tiffs = [rio.open_rasterio(tif, chunks=chunksize)[0] for tif in tiffs]
#             # build stack
#             tiffs = xr.concat(tiffs, dim='date')
#             tiffs['date'] = pd.to_datetime(dates)
#             # 2 and 4 multipliers to have the same values as in SLC
#             if intensity:
#                 stack.append((2*DFACT*np.abs(tiffs))**2)
#             else:
#                 stack.append(2*DFACT*tiffs)
# 
#         return stacks if subswath is None else stacks[0]

    def open_cube(self, name, chunksize=None):
        """
        Opens an xarray 3D Dataset from a NetCDF file and re-chunks it based on the specified chunksize.

        This function takes the name of the model to be opened, reads the NetCDF file, and re-chunks
        the dataset according to the provided chunksize or the default value from the 'stack' object.
        The 'date' dimension is always chunked with a size of 1.

        Parameters
        ----------
        name : str
            The name of the model file to be opened.
        chunksize : int, optional
            The chunk size to be used for dimensions other than 'date'. If not provided, the default
            chunk size from the 'stack' object will be used.

        Returns
        -------
        xarray.Dataset
            The re-chunked xarray Dataset read from the specified NetCDF file.

        """
        import xarray as xr
        import pandas as pd
        import os

        if chunksize is None:
            chunksize = self.chunksize

        model_filename = self.get_filename(name, add_subswath=False)
        assert os.path.exists(model_filename), f'ERROR: The NetCDF file is missed: {model_filename}'

        # Open the dataset without chunking
        model = xr.open_dataset(model_filename, engine=self.engine)
        chunks = {dim: 1 if dim == 'date' else chunksize for dim in model.dims}
        # Re-chunk the dataset using the chunks dictionary
        model = model.chunk(chunks)

        # convert string dates to dates
        if 'date' in model.dims:
            model['date'] = pd.to_datetime(model['date'].values)
    
        if 'yy' in model.dims and 'xx' in model.dims:
            model = model.rename({'yy': 'lat', 'xx': 'lon'})

        if 'a' in model.dims and 'r' in model.dims:
            model = model.rename({'a': 'y', 'r': 'x'})

        # in case of a single variable return DataArray
        if len(model.data_vars) == 1:
            return model[list(model.data_vars)[0]]
        return model

    def save_cube(self, model, name=None, caption='Saving 3D datacube', chunksize=None, debug=False):
        """
        Save an xarray 3D Dataset to a NetCDF file and re-chunks it based on the specified chunksize.

        The 'date' dimension is always chunked with a size of 1.

        Parameters
        ----------
        model : xarray.Dataset
            The model to be saved.
        chunksize : int, optional
            The chunk size to be used for dimensions other than 'date'. If not provided, the default
            chunk size from the 'stack' object will be used.
        caption: str
            The text caption for the saving progress bar.

        Returns
        -------
        None
        """
        import xarray as xr
        import dask
        import os

        if chunksize is None:
            chunksize = self.chunksize

        if name is None and isinstance(model, xr.DataArray):
            assert model.name is not None, 'Define the grid name or use name argument for the NetCDF filename'
            name = model.name
        elif name is None:
            raise ValueError('Specify name for the output NetCDF file')
        
        # save to NetCDF file
        model_filename = self.get_filename(name, add_subswath=False)
        if os.path.exists(model_filename):
            os.remove(model_filename)
        if isinstance(model, xr.DataArray):
            if debug:
                print ('DEBUG: DataArray')
            netcdf_compression = self.compression(model.shape, chunksize=(1, chunksize, chunksize))
            encoding = {model.name: netcdf_compression}
        elif isinstance(model, xr.Dataset):
            if debug:
                print ('DEBUG: Dataset')
            if len(model.dims) == 3:
                encoding = {varname: self.compression(model[varname].shape, chunksize=(1, chunksize, chunksize)) for varname in model.data_vars}
            else:
                encoding = {varname: self.compression(model[varname].shape, chunksize=chunksize) for varname in model.data_vars}
        delayed = model.to_netcdf(model_filename,
                         engine=self.engine,
                         encoding=encoding,
                         compute=False)
        tqdm_dask(dask.persist(delayed), desc=caption)
        # cleanup - sometimes writing NetCDF handlers are not closed immediately and block reading access
        import gc; gc.collect()
