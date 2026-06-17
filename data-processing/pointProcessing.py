import numpy as np
import scipy as sp
import shapely as shp
import quadpy as qp
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

import TIFFretrieval


dataset = TIFFretrieval.getTestArray()

# For each array we interpolate values and store
# the corresponding spline and its spline derivatives.

bivariateSplineSurface = sp.interpolate.RectBivariateSpline(np.arange(5000), np.arange(5000), dataset)
f_x  = bivariateSplineSurface.partial_derivative(1, 0)
f_y  = bivariateSplineSurface.partial_derivative(0, 1)
f_xy = bivariateSplineSurface.partial_derivative(1, 1)
f_xx = bivariateSplineSurface.partial_derivative(2, 0)
f_yy = bivariateSplineSurface.partial_derivative(0, 2)

# =========================================================================
print("breakpoint 1 passed")


scheme = qp.t2.get_good_scheme(7)
def quadrature(function, triangulatedPolygons):
    polygonArea = np.zeros(3)

    for triangle in triangulatedPolygons:
        Q = scheme.integrate(function, np.array(triangle).T)
        polygonArea += Q

    return polygonArea



# The meanCurvature function is not called directly,
# but is passed to the quadrature function in the CVT loop.

def meanCurvature(coords):

    x = coords[0]
    y = coords[1]

    bounds = (x<0) | (x>4999) | (y<0) | (y>4999)

    evfx  =  f_x(x, y, grid=False)
    evfy  =  f_y(x, y, grid=False)
    evfxy = f_xy(x, y, grid=False)
    evfxx = f_xx(x, y, grid=False)
    evfyy = f_yy(x, y, grid=False)

    H = ( (1 + evfy**2)*evfxx - 2*(evfx)*(evfy)*(evfxy) + (1 + evfx**2)*evfyy ) / ( 2*(1 + evfx**2 + evfy**2)**(3/2) )

    H = np.abs(H) + 1e-6
    H = np.where(bounds, 0.0, H)

    return [H, H*x, H*y]



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



# =========================================================================
print("breakpoint 2 passed")



def plotVoronoi(generatorPoints, voronoiPolygons, ax):

    ax.clear()

    polygonLines = LineCollection([np.array(polygon.exterior.coords) for polygon in voronoiPolygons], linewidths=1)
    ax.add_collection(polygonLines)

    ax.scatter(np.array(generatorPoints)[:, 0], np.array(generatorPoints)[:, 1])

    ax.set_xlim(0, 5000)
    ax.set_ylim(0, 5000)

    plt.pause(0.0001)


# ============================= Main function =============================
def centroidalVoronoiTessellation():

    # Initial Sampling + Tessellation:
    sampler = sp.stats.qmc.PoissonDisk(d=2, radius=0.0125)
    generatorPoints = sampler.random(n=400)
    generatorPoints *= 5000

    boundary = shp.box(0, 0, 5000, 5000)
    shpVoronoiPolygons = shp.voronoi_polygons(shp.multipoints(generatorPoints), ordered=True)
    voronoiPolygons = [polygon.intersection(boundary) for polygon in shpVoronoiPolygons.geoms]

    plt.ion()
    fig, ax = plt.subplots(figsize=(10,10))
    plotVoronoi(generatorPoints, voronoiPolygons, ax)



    # =====================================================================
    print("breakpoint 3 passed")




    # CVT Loop
    history = []
    rollingAverageGradient = np.inf
    iteration = 0
    while rollingAverageGradient > 1e-4 and iteration < 2500:

        oldGeneratorPoints = np.array(generatorPoints)
        weightedPoints = []

        triangulatedPolygons = triangulatePolygons(voronoiPolygons)

        for triangulatedPolygon in triangulatedPolygons:
            meanCurvatureWeighting = quadrature(meanCurvature, triangulatedPolygon)
            weightedPoints.append([meanCurvatureWeighting[1]/meanCurvatureWeighting[0],
                                   meanCurvatureWeighting[2]/meanCurvatureWeighting[0]])

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



centroidalVoronoiTessellation()




# =========================================================================
print("breakpoint 5 passed, file complete")
