import numpy as np
import pandas as pd
from pathlib import Path
import rasterio as rio

extension = "/Volumes/Expansion/DTM England/"

ordnanceGrid = { "NT" : (0,2),  "NU" : (1,2),  "OQ" : (2,2),
                 "NY" : (0,1),  "NZ" : (1,1),  "OV" : (2,1),
                 "SD" : (0,0),  "SE" : (1,0),  "TA" : (2,0)
               }

quadrantOffset = { "nw" : (0,1),  "ne" : (1,1),
                   "sw" : (0,0),  "se" : (1,0)
                  }

quadrantOffsetLookup = { value:key for key, value in quadrantOffset.items() }
ordnanceGridLookup   =  { value:key for key, value in ordnanceGrid.items() }

def retrieveFilteredList():

    correctSuffix = ".tif"
    correctGridValues = list(ordnanceGrid.keys())
    folder = Path(extension)

    files = [filename for filename in folder.glob(f"*{correctSuffix}") if filename.name[:2] in correctGridValues]

    return files

def parseFileName(filename):

    gridValue   = filename[:2]
    subGridValue = filename[2:4]
    quadrantValue = filename[4:6]

    return gridValue, subGridValue, quadrantValue

def toGlobalCoords(gridValue, subGridValue, quadrantValue):

    gridX = 20 * ordnanceGrid[gridValue][0]
    gridY = 20 * ordnanceGrid[gridValue][1]
    subGridX = 2 * int(subGridValue[0])
    subGridY = 2 * int(subGridValue[1])
    quadrantX = quadrantOffset[quadrantValue][0]
    quadrantY = quadrantOffset[quadrantValue][1]

    x = gridX + subGridX + quadrantX
    y = gridY + subGridY + quadrantY

    return (x, y)

def fromGlobalCoords(x, y):

    quadrantX = x % 2
    quadrantY = y % 2
    subGridX = (x // 2) % 10
    subGridY = (y // 2) % 10
    gridX = (x // 2) // 10
    gridY = (y // 2) // 10

    gridValue = ordnanceGridLookup[(gridX, gridY)]
    subGridValue = f"{subGridX}{subGridY}"
    quadrantValue = quadrantOffsetLookup[(quadrantX, quadrantY)]

    suffix = "_DTM_1m.tif"
    string = gridValue + subGridValue + quadrantValue + suffix

    return string

def getTileGroup(filename):

    gridValue, subGridValue, quadrantValue = parseFileName(filename)

    x,y = toGlobalCoords(gridValue, subGridValue, quadrantValue)

    tileGroup = { fromGlobalCoords(x+dx, y+dy) : (x+dx, y+dy) for dx in [-1, 0, 1] for dy in (-1, 0, 1)}

    return tileGroup

def readFile(filename):

    path = Path(extension) / filename

    if not path.exists():
        return None

    dataset = rio.open(path)
    band1 = dataset.read(1)
    array = np.flipud(band1)

    return array

def concatArrays(tileGroup):

    coordinates = sorted(list(tileGroup.items()))
    xAxis = sorted(set( x for x, y in coordinates))
    yAxis = sorted(set( y for x, y in coordinates))

    grid = []

    for y in yAxis:

        row = []

        for x in xAxis:

            filename = fromGlobalCoords(x,y)
            row.append(readFile(filename))

        grid.append(row)

    return np.block(grid)

def formatTileGroups(fileList):

    croppedArrays = []

    for file in fileList:

        tileGroup = getTileGroup(file)
        array = concatArrays(tileGroup)
        croppedArray = array[2500:12500, 2500:12500]
        croppedArrays.append(croppedArray)

    return croppedArrays

files = retrieveFilteredList()
processedArrays = formatTileGroups(files)
