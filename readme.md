## Toolset for Project "Leveraging Vision Reconstruction Pipelines for Satellite Imagery"

Website: https://kai-46.github.io/VisSat/

This toolset is python-based. It uses python3 instead of python2.

If you use linux-based system, you need to first install gdal:
```{r, engine='bash', count_lines}
    sudo apt-get install libgdal-dev gdal-bin
    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal
```

Then all the dependent packages can be installed via:
```{r, engine='bash', count_lines}
    pip3 install -r requirements.txt
```

Usage:
```{r, engine='bash', count_lines}
    python3 main.py --data_dir {path to the data we provide} --ply {path to your reconstructed point cloud} --out_dir {output directory}
```

After the program finishes running, you will see inside the {output directory}:
    
    * point_cloud.ply: points' coordinates are in (UTM east, UTM north, altitude) coordinate system
    * dsm.tif: GeoTiff file produced from your point cloud; you can open it with QGIS
    * dsm.jpg: preview for dsm.tif
    * dsm.cbar.jpg: color bar for dsm.jpg; the unit is meter

If you would like to evaluate the accuracy of your point cloud, simply enable the --eval flag, i.e.,
```{r, engine='bash', count_lines}
    python3 main.py --eval --data_dir {path to the data we provide} --ply {path to your reconstructed point cloud} --out_dir {output directory}
```

Then you will see the following additional files inside the {output directory}:

    * offset.txt: this contains the median error and completeness score for your point cloud
    * source_after_align.jpg: this is your height map aligned to the ground-truth
    * source_after_align.cbar.jpg: color bar for source_after_align.jpg; unit is meter
    * target_after_align.jpg: this is the ground-truth height map
    * target_after_align.cbar.jpg: color bar for target_after_align.jpg; unit is meter
    * error_map.jpg: this is the error map
    * error_map.cbar.jpg: color bar for error_map.jpg; unit is meter
    * error_dist.jpg: distrubution of the errors

---

If you would like to skew-correct the images, you can use,
```{r, engine='bash', count_lines}
    python3 skew_correct.py --data_dir {path to the data we provide}
```

You will see the skew-corrected images along with camera parameters inside {data_dir}/skew_correct/.

---
Note that for perspective cameras with non-zero skew, the camera parameters are listed as:

```math
w, h, f_x, f_y, c_x, c_y, s, q_w, q_x, q_y, q_z, t_x, t_y, t_z
```
, while for pinhole cameras with zero skew, the camera parameters are listed as:

```math
w, h, f_x, f_y, c_x, c_y, q_w, q_x, q_y, q_z, t_x, t_y, t_z
```