# ----------------------------------------------------------------------------
# PyGMTSAR
# 
# This file is part of the PyGMTSAR project: https://github.com/mobigroup/gmtsar
# 
# Copyright (c) 2021, Alexey Pechnikov
# 
# Licensed under the BSD 3-Clause License (see LICENSE for details)
# ----------------------------------------------------------------------------
from .Stack_reframe_gmtsar import Stack_reframe_gmtsar
from .S1 import S1
from .PRM import PRM

class Stack_reframe(Stack_reframe_gmtsar):

    def _reframe_subswath(self, subswath, date, geometry, debug=False):
        """
        Estimate framed area using Sentinel-1 GCPs approximation.

        Parameters
        ----------
        subswath : int
            The subswath number.
        date : str
            The date of the scene.
        geometry: shapely.geometry of geopandas.GeoSeries or geopandas.GeoDataFrame
            Optional geometry covering required bursts to crop the area.
        debug : bool, optional
            Enable debug mode. Default is False.

        Returns
        -------
        pandas.DataFrame
            The updated DataFrame with the estimated framed area.

        Examples
        --------
        df = stack.reframe(1, '2023-05-20')
        """
        import geopandas as gpd
        import numpy as np
        #import shapely
        from shapely.geometry import Point, LineString, Polygon, MultiPolygon
        from shapely.ops import cascaded_union
        from datetime import datetime, timedelta
        import os
        import xmltodict
        import copy
        import warnings
        warnings.filterwarnings('ignore')

        # define line covering some bursts to crop them
        if isinstance(geometry, (gpd.GeoDataFrame, gpd.GeoSeries)):
            # it does not work with numpy 2.0.0 for geometry.minimum_rotated_rectangle
            geometry = geometry.union_all()
        assert not geometry is None, f'ERROR: subswath {subswath} is not covered, you need to exclude it.'

        # convert to polygon when possible
        geometry = geometry.minimum_rotated_rectangle
        # it can be point or line or polygon
        if isinstance(geometry, Point):
            # create ~100m buffer around
            #geometry = geometry.buffer(1e-3)
            raise ValueError(f"Unsupported Point geometry. Unfortunately, GMTSAR tools cannot crop a scene to a single burst.")
        if isinstance(geometry, Polygon):
            rect = geometry.exterior
            # define diagonal line
            diag1 = LineString([rect.coords[0], rect.coords[2]])
            diag2 = LineString([rect.coords[1], rect.coords[3]])
            if diag1.length <= diag2.length:
                geometry = diag1
            else:
                geometry = diag2
        if debug:
            print ('DEBUG: geometry', geometry)

        df = self.get_repeat(subswath, date)
        if debug:
            print('DEBUG: reframe scenes: ', len(df))
        prefix = self.get_subswath_prefix(subswath, date)
        if debug:
            print ('DEBUG: ','prefix', prefix)

        old_filename = os.path.join(self.basedir, f'{prefix}')
        #print ('old_filename', old_filename)

        self._make_s1a_tops(subswath, date, debug=debug)
        prm = PRM.from_file(old_filename+'.PRM')
        if debug:
            print ('DEBUG: ','geometry', geometry)
        tmpazi_a = prm.SAT_llt2rat([geometry.coords[0][0],  geometry.coords[0][1],  0], precise=1, debug=debug)[1]
        tmpazi_b = prm.SAT_llt2rat([geometry.coords[-1][0], geometry.coords[-1][1], 0], precise=1, debug=debug)[1]
        tmpazi = min(tmpazi_a, tmpazi_b)
        if debug:
            print ('DEBUG: ','tmpazi', tmpazi)
        prm.shift_atime(tmpazi, inplace=True).update()
        azi_a = prm.SAT_llt2rat([geometry.coords[0][0], geometry.coords[0][1], 0], precise=1, debug=debug)[1] + tmpazi
        azi_b = prm.SAT_llt2rat([geometry.coords[-1][0], geometry.coords[-1][1], 0], precise=1, debug=debug)[1] + tmpazi
        # reorder boundaries for orbit
        azi1 = min(azi_a, azi_b)
        azi2 = max(azi_a, azi_b)
        if debug:
            print ('DEBUG: ','azi1', azi1, 'azi2', azi2)

        # Working on bursts covering $azi1 ($ll1) - $azi2 ($ll2)...
        #print ('_assemble_tops', subswath, date, azi1, azi2, debug)
        self._assemble_tops(subswath, date, azi1, azi2, debug=debug)

        # Parse new .xml to define new scene name
        # like to 's1b-iw3-slc-vv-20171117t145922-20171117t145944-008323-00ebab-006'
        filename = os.path.splitext(os.path.split(df['datapath'].iloc[0])[-1])[0]
        head1 = filename[:15]
        tail1 = filename[-17:]
        xml_header = S1.read_annotation(old_filename+'.xml')['product']['adsHeader']
        date_new = xml_header['startTime'][:10].replace('-','')
        t1 = xml_header['startTime'][11:19].replace(':','')
        t2 = xml_header['stopTime'][11:19].replace(':','')
        new_name = f'{head1}{date_new}t{t1}-{date_new}t{t2}-{tail1}'
        new_filename = os.path.join(self.basedir, new_name)
        #print ('new_filename', new_filename)

        # rename xml and tiff
        for ext in ['.tiff', '.xml']:
            if debug:
                print('DEBUG: rename', old_filename+ext, new_filename+ext)
            os.rename(old_filename+ext, new_filename+ext)

        # cleanup
        for fname in [old_filename+'.LED', old_filename+'.PRM']:
            if not os.path.exists(fname):
                continue
            if debug:
                print ('DEBUG: remove', fname)
            os.remove(fname)

        # update and return only one record
        out = df.head(1)
        #df['datetime'] = self.text2date(f'{date_new}t{t1}', False)
        out['datetime'] = datetime.strptime(f'{date_new}T{t1}', '%Y%m%dT%H%M%S')
        out['metapath'] = new_filename + '.xml'
        out['datapath'] = new_filename + '.tiff'
        # update approximate location
        out['geometry'] = cascaded_union([geom for multi_polygon in df.geometry for geom in multi_polygon.geoms
                                      if geom.intersects(geometry)])

        # merge calibration xml files

#         # define burst size
#         with open(df.metapath[0], 'r') as file:
#             xml = xmltodict.parse(file.read())
#         imageInformation = xml['product']['imageAnnotation']['imageInformation']
#         numberOfLines = int(imageInformation['numberOfLines'])

        if 'noisepath' in df and not df['noisepath'].isnull().sum():
            # different schemes
            tags = ['Range', '']
            xml_files = df[f'noisepath']

            startTimes = []
            stopTimes = []
            # collect unique range vectors only and ignore 3 duplicated before and after
            range_vectors = {}
            azimuth_vectors = []
            for xml_file in xml_files:
                with open(xml_file, 'r') as file:
                    xml = xmltodict.parse(file.read())
                # modify tag data without affecting 'xml'
                noise = copy.deepcopy(xml['noise'])
                adsHeader = noise['adsHeader']
                startTimes.append(adsHeader['startTime'])
                stopTimes.append(adsHeader['stopTime'])
                # find only one included subtag
                tag = [tag for tag in tags if f'noise{tag}VectorList' in noise]
                assert len(tag)>0, 'ERROR: not found range noise vectors'
                assert len(tag)==1, 'ERROR: found multiple declarations for range noise vector'
                tag = tag[0]
                # read multiple range vectors for unique azimuths
                for vector in noise[f'noise{tag}VectorList'][f'noise{tag}Vector']:
                    range_vectors[vector['azimuthTime']] = vector
                # read one or zero azimuth vector
                if 'noiseAzimuthVectorList' in noise:
                    azimuth_vectors.append(noise['noiseAzimuthVectorList']['noiseAzimuthVector'])

            if len(azimuth_vectors):
                # Convert string to datetime object
                start_dts = [datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f') for dt in startTimes]
                stop_dts = [datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f') for dt in stopTimes]
                overlap_dts = [(stop_dt-start_dt)/2 for stop_dt, start_dt in zip(stop_dts[:1], start_dts[1:])]

                total = 0
                total_times = []
                total_values = []
                azimuth_vectors_new = []
                for start_dt, stop_dt, start_overlap_dt, stop_overlap_dt, azimuth_vector in \
                        zip(start_dts, stop_dts, [timedelta(0)] + overlap_dts, overlap_dts + [timedelta(0)], azimuth_vectors):
                    counter = int(azimuth_vector['lastAzimuthLine'])
                    total += counter + 1
                    count = int(azimuth_vector['line']['@count'])
                    interval = (stop_dt - start_dt).total_seconds()
                    delta = interval/counter
                    #print ('delta', delta)

                    # read line numbers
                    lines = azimuth_vector['line']['#text'].split(' ')
                    # convert line numbers to times
                    times = [start_dt + timedelta(seconds=(float(l) * delta)) for l in lines]
                    # read lut values
                    values = np.array(azimuth_vector['noiseAzimuthLut']['#text'].split(' ')).astype(float)

                    # mask out items for bursts intersections
                    start_mask = np.array(times) - times[0] >= start_overlap_dt
                    stop_mask = times[-1] - np.array(times) >= stop_overlap_dt
                    # filter out values for burst intersection
                    total_times.extend(np.array(times)[start_mask & stop_mask])
                    total_values.extend(values[start_mask & stop_mask])

                # convert times to line numbers
                total_lines = [np.round((t - start_dts[0]).total_seconds()/delta).astype(int) for t in total_times]

                # modify tag data without affecting 'xml'
                noiseAzimuthVector = copy.deepcopy(noise['noiseAzimuthVectorList']['noiseAzimuthVector'])
                noiseAzimuthVector['lastAzimuthLine'] = total - 1
                noiseAzimuthVector['line']['@count'] = len(total_lines)
                noiseAzimuthVector['line']['#text'] = ' '.join(map(str, total_lines))
                noiseAzimuthVector['noiseAzimuthLut']['@count'] = len(total_values)
                noiseAzimuthVector['noiseAzimuthLut']['#text'] = ' '.join(map(str, total_values))

            # build new xml
            noise['adsHeader']['startTime'] = min(startTimes)
            noise['adsHeader']['stopTime'] = max(stopTimes)
            noise[f'noise{tag}VectorList']['@count'] = len(range_vectors)
            noise[f'noise{tag}VectorList'][f'noise{tag}Vector'] = list(range_vectors.values())
            if len(azimuth_vectors):
                noise['noiseAzimuthVectorList']['noiseAzimuthVector'] = noiseAzimuthVector

            # save to new xml file
            new_xml_file = os.path.join(self.basedir, f'noise-{new_name}.xml')
            with open(new_xml_file, 'w') as file:
                file.write(xmltodict.unparse({'noise': noise}, pretty=True, indent='  '))

            out['noisepath'] = new_xml_file

        if 'calibpath' in df and not df['calibpath'].isnull().sum():
            startTimes = []
            stopTimes = []
            # collect unique vectors only and ignore 3 duplicated before and after
            calibrationVectors = {}
            for xml_file in df.calibpath:
                with open(xml_file, 'r') as file:
                    xml = xmltodict.parse(file.read())
                # modify 'calibration' without affecting 'xml'
                calibration = copy.deepcopy(xml['calibration'])
                adsHeader = calibration['adsHeader']
                startTimes.append(adsHeader['startTime'])
                stopTimes.append(adsHeader['stopTime'])
                for calibrationVector in calibration['calibrationVectorList']['calibrationVector']:
                    calibrationVectors[calibrationVector['azimuthTime']] = calibrationVector
            calibration['adsHeader']['startTime'] = min(startTimes)
            calibration['adsHeader']['stopTime'] = max(stopTimes)
            calibration['calibrationVectorList']['@count'] = len(calibrationVectors)
            calibration['calibrationVectorList']['calibrationVector'] = list(calibrationVectors.values())

            new_xml_file = os.path.join(self.basedir, 'calibration-' + new_name + '.xml')
            with open(new_xml_file, 'w') as file:
                file.write(xmltodict.unparse({'calibration': calibration}, pretty=True, indent='  '))

            out['calibpath'] = new_xml_file

        return out

    def compute_reframe(self, geometry=None, n_jobs=-1, queue=16, caption='Reframing', **kwargs):
        """
        Reorder bursts from sequential scenes to cover the full orbit area or some bursts only.

        Parameters
        ----------
        geometry: shapely.geometry of geopandas.GeoSeries or geopandas.GeoDataFrame
            Optional geometry covering required bursts to crop the area.
        n_jobs : int, optional
            Number of parallel processing jobs. n_jobs=-1 means all the processor cores are used.

        Returns
        -------
        None

        Examples
        --------
        Without defined geometry the command is silently skipped:
        stack.reframe()
        
        Define a line partially covering two bursts:
        stack.reframe(geometry=LineString([Point(25.3, 35.0), Point(25, 35.2)]))
        
        Read the geometry from GeoJSON file and convert to WGS84 coordinates:
        AOI = gpd.GeoDataFrame().from_file('AOI.json').to_crs(4326)
        stack.reframe(geometry=AOI)
        
        TODO: Define a point on a selected burst (this option is not available now):
        stack.reframe(geometry=Point(25.3, 35))
        """
        from tqdm.auto import tqdm
        import joblib
        import pandas as pd

        if n_jobs is None or ('debug' in kwargs and kwargs['debug'] == True):
            print ('Note: sequential joblib processing is applied when "n_jobs" is None or "debug" is True.')
            joblib_backend = 'sequential'
        else:
            joblib_backend = 'loky'
            
        dates = self.df.index.unique().values
        subswaths = self.get_subswaths()
        # approximate subswath geometries from GCP
        geometries = {subswath: self.df[self.df.subswath==subswath].geometry.union_all() for subswath in subswaths}

        records = []
        # Applying iterative processing to prevent Dask scheduler deadlocks.
        stacksize = len(dates)
        counter = 0
        digits = len(str(stacksize))
        # Splitting all the dates into chunks, each containing approximately queue dates.
        #n_chunks = stacksize // queue if stacksize > queue else 1
        if stacksize > queue:
            chunks = [dates[i:i + queue] for i in range(0, stacksize, queue)]
            n_chunks = len(chunks)
        else:
            chunks = [dates]
            n_chunks = 1
        for chunk in chunks:
            if n_chunks > 1:
                chunk_caption = f'{caption}: {(counter+1):0{digits}}...{(counter+len(chunk)):0{digits}} from {stacksize}'
            else:
                chunk_caption = caption
            
            if joblib_backend == 'loky':
                # can be missed on some systems
                from joblib.externals import loky
                loky.get_reusable_executor(kill_workers=True).shutdown(wait=True)
            with self.tqdm_joblib(tqdm(desc=chunk_caption, total=len(chunk)*len(subswaths))) as progress_bar:
                chunk_records = joblib.Parallel(n_jobs=n_jobs, backend=joblib_backend)(joblib.delayed(self._reframe_subswath)\
                                (subswath, date,
                                geometry.intersection(geometries[subswath]) if geometry is not None else geometries[subswath],
                                **kwargs) for date in chunk for subswath in subswaths)
                records.extend(chunk_records)
            counter += len(chunk)

        self.df = pd.concat(records)
