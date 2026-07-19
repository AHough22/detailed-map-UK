from ast import Break

import numpy as np
import scipy as sp
import shapely as shp
import quadpy as qp
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

import TIFFretrieval

dataset = TIFFretrieval.getTestArray()
dataset = np.flipud(dataset)

# For each array we interpolate values and store
# the corresponding spline and its spline derivatives.

bivariateSplineSurface = sp.interpolate.RectBivariateSpline(np.arange(5000), np.arange(5000), dataset)

f_x  = bivariateSplineSurface.partial_derivative(1, 0)
f_y  = bivariateSplineSurface.partial_derivative(0, 1)
f_xy = bivariateSplineSurface.partial_derivative(1, 1)
f_xx = bivariateSplineSurface.partial_derivative(2, 0)
f_yy = bivariateSplineSurface.partial_derivative(0, 2)

# The meanCurvature function is not called directly,
# but is passed to the quadrature function in the CVT loop.

def meanCurvature(coords):

    x = coords[0]
    y = coords[1]

    evfx  =  f_x(y, x, grid=False)
    evfy  =  f_y(y, x, grid=False)
    evfxy = f_xy(y, x, grid=False)
    evfxx = f_xx(y, x, grid=False)
    evfyy = f_yy(y, x, grid=False)

    H = ( (1 + evfy**2)*evfxx - 2*(evfx)*(evfy)*(evfxy) + (1 + evfx**2)*evfyy ) / ( 2*(1 + evfx**2 + evfy**2)**(3/2) )

    H = np.abs(H) + 1e-6

    return H

def calculateWeightMap():

    x = np.arange(5000)
    y = np.arange(5000)
    meshgrid = np.meshgrid(x, y)

    fullMeanCurvature = meanCurvature(meshgrid)

    evfx  =  f_x(y, x)
    evfy  =  f_y(y, x)

    magnitude = np.sqrt(evfx**2 + evfy**2)

    magnitudeBlur1 = sp.ndimage.gaussian_filter(magnitude, 800)
    magnitudeBlur2 = sp.ndimage.gaussian_filter(magnitude, 400)
    magnitudeBlur3 = sp.ndimage.gaussian_filter(magnitude, 200)
    magnitudeBlur4 = sp.ndimage.gaussian_filter(magnitude, 100)

    magnitudeBlurred = (magnitudeBlur1 + magnitudeBlur2 + magnitudeBlur3 + magnitudeBlur4) / 4

    fullMeanCurvature = sp.ndimage.minimum_filter(fullMeanCurvature, 20)
    fullMeanCurvature = sp.ndimage.gaussian_filter(fullMeanCurvature, 200)

    multiplication = magnitudeBlurred * fullMeanCurvature
    weightedMap = multiplication / np.max(multiplication)
    return weightedMap

calculatedWeightMap = calculateWeightMap()
weightedMap = sp.interpolate.RectBivariateSpline(np.arange(5000), np.arange(5000), calculatedWeightMap)

def weightMapRetrieval(coords):

    x = coords[0]
    y = coords[1]
    bounds = (x<0) | (x>4999) | (y<0) | (y>4999)
    W = weightedMap(y, x, grid=False)
    W = np.where(bounds, 0.0, W)
    W = np.maximum(1e-6, W)

    return [W, W*x, W*y]

def triangulatePolygons(polygons):

    triangulatedPolygons = []

    for polygon in polygons:

        triangles = []
        centroid = polygon.centroid.coords[0]

        for i in range(len(polygon.exterior.coords)-1):
            triangles.append([
                             [polygon.exterior.coords[i][0], polygon.exterior.coords[i+1][0], centroid[0]],
                             [polygon.exterior.coords[i][1], polygon.exterior.coords[i+1][1], centroid[1]]
                             ])
        triangulatedPolygons.append(triangles)

    return triangulatedPolygons

def plotVoronoi(generatorPoints, voronoiPolygons, ax):

    ax.clear()

    polygonLines = LineCollection([np.array(polygon.exterior.coords) for polygon in voronoiPolygons], linewidths=1)
    ax.add_collection(polygonLines)

    ax.scatter(np.array(generatorPoints)[:, 0], np.array(generatorPoints)[:, 1])

    ax.set_xlim(0, 5000)
    ax.set_ylim(0, 5000)

    plt.pause(0.0001)

def poissonDiscSampling():

    samplePoints = []
    activePoints = []
    pointLimit   = 60

# Initialise the first sample point:
# Coords: 2500 ±250

    x = 250*np.random.rand()+2250
    y = 250*np.random.rand()+2250

    newPointIndex = 0
    samplePoints.append([x, y, 0])
    activePoints.append(newPointIndex)

# Loop to generate new points:
    while len(activePoints) > 0 and len(samplePoints) < 400:

        # While there are active points, sample a point from the active points
        # and generate a new point arounds its annulus

        pointIndex = np.random.choice(activePoints)

        coords = samplePoints[pointIndex][:-1]         # (x,y)

        radius = 50/(weightMapRetrieval(coords)[0])         # Radius inversely proportional to the weight map value
        distance = (np.random.rand()*radius)+radius    # Keeps distance between radius, 2*radius
        angle = np.random.rand() * 2*np.pi             # Random angle between 0 and 2*pi

        newPointCoords = distance * np.array([np.cos(angle), np.sin(angle)]) + np.array(coords)

        # Check if the new point is outside the map bounds

        if not ((0 < newPointCoords[0] < 5000) and (0 < newPointCoords[1] < 5000)):
            samplePoints[pointIndex][2] += 0.1
            if (samplePoints[pointIndex][2] >= pointLimit) and (pointIndex in activePoints):
                activePoints.remove(pointIndex)
            continue

        # Check if any existing point is within the annulus of the new point

        distanceViolation = False

        for i in range(len(samplePoints)):

            existingPoint = samplePoints[i][:-1]
            pointDistance = np.linalg.norm(np.array(newPointCoords) - np.array(existingPoint))
            newPointRadius = 50/(weightMapRetrieval(np.array(existingPoint))[0])

            if (pointDistance < newPointRadius):
                samplePoints[pointIndex][2] += 1
                if samplePoints[pointIndex][2] >= pointLimit and i in activePoints:
                    activePoints.remove(i)
                distanceViolation = True
                break



        # Add the new point to the sample if no distance violation was found

        if not distanceViolation:

            newPointIndex += 1
            samplePoints.append([newPointCoords[0], newPointCoords[1], 0])
            activePoints.append(newPointIndex)
            print("Point ", newPointIndex, " added")

    return np.array(samplePoints)[:, :2]

def showPoissonDiscSample():

    samplePoints = poissonDiscSampling()
    fig, ax = plt.subplots(figsize=(10,10))
    ax.scatter(samplePoints[:, 0], samplePoints[:, 1])
    ax.set_ylim(0,5000)
    ax.set_xlim(0,5000)
    plt.show()

scheme = qp.t2.get_good_scheme(7)
def quadrature(function, triangulatedPolygons):
    polygonArea = np.zeros(3)

    for triangle in triangulatedPolygons:
        Q = scheme.integrate(function, np.array(triangle).T)
        polygonArea += Q

    return polygonArea

def centroidalVoronoiTessellation():

    # Initial Sampling + Tessellation:
    generatorPoints = poissonDiscSampling()

    boundary = shp.box(0, 0, 5000, 5000)
    shpVoronoiPolygons = shp.voronoi_polygons(shp.multipoints(generatorPoints), ordered=True)
    voronoiPolygons = [polygon.intersection(boundary) for polygon in shpVoronoiPolygons.geoms]

    plt.ion()
    fig, ax = plt.subplots(figsize=(10,10))
    plotVoronoi(generatorPoints, voronoiPolygons, ax)




    print("breakpoint 3 passed")




    # CVT Loop
    history = []
    rollingAverageGradient = np.inf
    iteration = 0
    while rollingAverageGradient > 1e-8 and iteration < 2500:

        oldGeneratorPoints = np.array(generatorPoints)
        weightedPoints = []

        triangulatedPolygons = triangulatePolygons(voronoiPolygons)

        for triangulatedPolygon in triangulatedPolygons:

            w, wx, wy = quadrature(weightMapRetrieval, triangulatedPolygon)
            weightedPoints.append([wx/w, wy/w])

        generatorPoints = np.clip(weightedPoints, 0.01, 4999.99)

        shpVoronoiPolygons = shp.voronoi_polygons(shp.multipoints(generatorPoints), ordered=True)
        voronoiPolygons = [polygon.intersection(boundary) for polygon in shpVoronoiPolygons.geoms]

        difference = np.linalg.norm(np.array(generatorPoints) - np.array(oldGeneratorPoints))
        history.append(difference)

        if len(history) > 10:
            history.pop(0)
        if len(history) >= 2:
            gradients = np.diff(history)
            rollingAverageGradient = np.abs(np.mean(gradients))

        if iteration % 10 == 0:
            plotVoronoi(generatorPoints, voronoiPolygons, ax)
            print("gradient =", rollingAverageGradient, "iteration =", iteration)

        iteration += 1

    plt.ioff()
    plt.show()

    return voronoiPolygons, generatorPoints

def showWeightedMap():
    fig, ax = plt.subplots(figsize=(10,10))
    ax.imshow(calculatedWeightMap, origin="lower")
    plt.show(block=False)
    plt.pause(0.001)

showWeightedMap()
centroidalVoronoiTessellation()


# =========================================================================
print("breakpoint 5 passed, file complete")
