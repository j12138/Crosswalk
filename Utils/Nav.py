import numpy as np

#Use the mean earth radius
EARTH_RADIUS = 6371008.0
from scipy.interpolate import splprep, splev,interp1d

def cross_track_distance(p1_lat, p1_lon, p2_lat, p2_lon, p3_lat, p3_lon):
    '''
    Determine the cross track distance (the distance of a point from a
    great-circle path).
    See: http://www.movable-type.co.uk/scripts/latlong.html#crossTrack
    d13 is distance from start point to third point
    b13 is (initial) bearing from start point to third point
    b12 is (initial) bearing from start point to end point
    :param p1_lat: The start latitude of the great-circle path.
    :type p1_lat: float or int
    :param p1_lon: The start longitude of the great-circle path.
    :type p1_lon: float or int
    :param p2_lat: The end latitude of the great-circle path.
    :type p2_lat: float or int
    :param p2_lon: The end longitude of the great-circle path.
    :type p2_lon: float or int
    :param p3_lat: The latitude to calculate cross-track error from.
    :type p3_lat: float or int
    :param p3_lon: The longitude to calculate cross-track error from.
    :type p3_lon: float or int
    :param units: The units in which to represent the distance. (default: meters)
    :type units: string
    :returns: The cross-track distance.
    :rtype: float
    '''
    d13 = great_circle_distance__haversine(p1_lat, p1_lon, p3_lat, p3_lon)
    b12 = np.radians(initial_bearing(p1_lat, p1_lon, p2_lat, p2_lon))
    b13 = np.radians(initial_bearing(p1_lat, p1_lon, p3_lat, p3_lon))
    value = np.arcsin(np.sin(d13 / EARTH_RADIUS) * np.sin(b13 - b12)) * EARTH_RADIUS
    return -value

def great_circle_distance__haversine(p1_lat, p1_lon, p2_lat, p2_lon):
    '''
    Determine the great-circle distance between two points using the
    Haversine formula.
    See: http://www.movable-type.co.uk/scripts/latlong.html
    :param p1_lat: The start latitude of the great-circle path.
    :type p1_lat: float or int
    :param p1_lon: The start longitude of the great-circle path.
    :type p1_lon: float or int
    :param p2_lat: The end latitude of the great-circle path.
    :type p2_lat: float_or_int
    :param p2_lon: The end longitude of the great-circle path.
    :type p2_lon: float_or_int
    :param units: The units in which to represent the distance. (default: meters)
    :type units: string
    :returns: The great-circle distance.
    :rtype: float
    '''
    sdlat2 = np.sin(np.radians(p1_lat - p2_lat) / 2.) ** 2
    sdlon2 = np.sin(np.radians(p1_lon - p2_lon) / 2.) ** 2
    a = sdlat2 + sdlon2 * np.cos(np.radians(p1_lat)) * np.cos(np.radians(p2_lat))
    value = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)) * EARTH_RADIUS
    return value

def initial_bearing(p1_lat, p1_lon, p2_lat, p2_lon):
    '''
    :param p1_lat: The start latitude of the great-circle path.
    :type p1_lat: float or int
    :param p1_lon: The start longitude of the great-circle path.
    :type p1_lon: float or int
    :param p2_lat: The end point latitude of the great-circle path.
    :type p2_lat: float or int
    :param p2_lon: The end point longitude of the great-circle path.
    :type p2_lon: float or int
    :returns: The initial bearing.
    :rtype: float
    '''
    dlon = np.radians(p2_lon - p1_lon)
    lat1 = np.radians(p1_lat)
    lat2 = np.radians(p2_lat)
    y = np.sin(dlon) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    return np.degrees(np.arctan2(y, x)) % 360


"""Compute the signed heading error between current and desired headings
# Arguments
    unit1: the desired heading
    unit2: the current heading
# Returns
    the signed error in degrees
"""
def compute_heading_error(unit1, unit2):
    phi = abs(unit2-unit1) % 360
    sign = 1
    "Compute the proper sign"
    if not ((unit1-unit2 >= 0 and unit1-unit2 <= 180) or (
            unit1-unit2 <= -180 and unit1-unit2 >= -360)):
        sign = -1
    if phi > 180:
        result = 360-phi
    else:
        result = phi
    
    return result*sign

#Get the location of a point with a distance and bearing from current lat,lon
def transform(lat1,lon1,bearing,distance):
    
    d=distance
    lat1 = np.radians(lat1) #Current lat point converted to radians
    lon1 = np.radians(lon1) #Current long point converted to radians
    brng= np.radians(bearing)
    
    lat2 = np.arcsin( np.sin(lat1)*np.cos(d/EARTH_RADIUS) +
                 np.cos(lat1)*np.sin(d/EARTH_RADIUS)*np.cos(brng))
    
    lon2 = lon1 + np.arctan2(np.sin(brng)*np.sin(d/EARTH_RADIUS)*np.cos(lat1),
                         np.cos(d/EARTH_RADIUS)-np.sin(lat1)*np.sin(lat2))
    
    return np.degrees(lat2),np.degrees(lon2)

#Interpolate a sparse set of lat lon using linear interpolation and a linear interpolant for velocity
def build_trajectory(lat,lon,vel,num_points):
    #https://stackoverflow.com/questions/31464345/fitting-a-closed-curve-to-a-set-of-points
    pts=np.vstack((lat,lon))
    tck, u = splprep(pts, u=None, s=0, per=0,k=1) 
    u_new = np.linspace(u.min(), u.max(), num_points)
    lat_interp,lon_interp = splev(u_new, tck, der=0)
    
    vels=interp1d(u,vel,kind='linear')
    vel_interp=vels(u_new)
    return lat_interp,lon_interp,vel_interp,pts
    





