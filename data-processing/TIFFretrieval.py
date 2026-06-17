import numpy as np
import pandas as pd
import rasterio as rio


def getTestArray():

    dataset = rio.open("/Volumes/Expansion/DTM England/NU01ne_DTM_1m.tif")
    band1 = dataset.read(1)
    return band1
