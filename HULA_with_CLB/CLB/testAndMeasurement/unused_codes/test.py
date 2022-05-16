import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

#Simulation window parameters
xMin=0;xMax=100;
yMin=0;yMax=1;
xDelta=xMax-xMin;yDelta=yMax-yMin; #rectangle dimensions
areaTotal=xDelta*yDelta;

#Point process parameters
lambda0=100; #intensity (ie mean density) of the Poisson process

#Simulate Poisson point process
numbPoints = scipy.stats.poisson( lambda0*xDelta ).rvs()#Poisson number of points
xx = xDelta*scipy.stats.uniform.rvs(0,1,((numbPoints,1)))+xMin#x coordinates of Poisson points
yy = yDelta*scipy.stats.uniform.rvs(0,1,((numbPoints,1)))+yMin#y coordinates of Poisson points
#Plotting
# plt.scatter(xx,yy, edgecolor='b', facecolor='none', alpha=0.5 )
# plt.xlabel("x"); plt.ylabel("y")
print(xx)