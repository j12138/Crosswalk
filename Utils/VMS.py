"""
Caravan VMS
By: Tyler Staudinger
"""
import numpy as np
import sys
#Change this to where you have installed X-Plane Connect
sys.path.append('/home/vader/Desktop/TaxiNet/XPlane/')
import xpc
import time
from PID import PID
from Nav import compute_heading_error,cross_track_distance,initial_bearing,great_circle_distance__haversine,transform


#Create class for the vehicle state, this class stores and updates states from xplane
class VehicleState:
    def __init__(self):
        self.client=xpc.XPlaneConnect(timeout=1000)
        self.lat=0.0 #Degrees
        self.lon=0.0 #Degrees
        self.heading=0.0 #Degrees
        self.groundspeed=0.0 #meters per second
        self.brake=0.0 #Binary 1 or 0
        self.front_wheel_lat=0.0 #Degrees
        self.front_wheel_lon=0.0 #Degrees
        self.rear_wheel_lat=0.0 #Degrees
        self.rear_wheel_lon=0.0 #Degrees
        #Distances are from the aircraft editor landing gear page converted to meters
        #These are distances from the aircraft default c.g. (point where ego state is measured from in xplane)
        self.dist_to_front_wheel=3.14 #Meters from default c.g.
        self.dist_to_rear_wheel=1.036 #Meters from default c.g.
        
    def reset_client(self):
        self.client=xpc.XPlaneConnect()
        
    def update_state(self):
        #Get the states of the aircraft
        drefs=["sim/flightmodel/position/latitude",
               "sim/flightmodel/position/longitude",
               "sim/flightmodel/position/psi",
               "sim/flightmodel/position/groundspeed",
               "sim/flightmodel/controls/parkbrake",
               ]
        states=np.squeeze(np.array(self.client.getDREFs(drefs)))
        self.lat=states[0]
        self.lon=states[1]
        self.heading=states[2]
        self.groundspeed=states[3]
        self.brake=states[4]
        #Compute the location of the front wheel
        self.front_wheel_lat,self.front_wheel_lon=transform(self.lat,self.lon,self.heading,self.dist_to_front_wheel)
        #Compute the location of the rear wheel
        #The rear wheel is behind the xplane default cg (reference point so we add 180 to the heading)
        self.rear_wheel_lat,self.rear_wheel_lon=transform(self.lat,self.lon,(self.heading+180.0),self.dist_to_rear_wheel)
        
    #Send our control to xplane
    def set_control(self,rudder,throttle):
        self.client.sendCTRL([0,0,rudder,throttle])
        
    #Set the brake in xplane
    def set_brake(self,brake):
        self.client.sendDREF("sim/flightmodel/controls/parkbrake", brake)
        
    #Reset the states of the airplane 
    def reset_plane(self,lat,lon,heading,altitude):
    
        #Null out all the velocity, acceleration etc variables
        drefs = ["sim/flightmodel/position/theta", "sim/flightmodel/position/phi","sim/flightmodel/position/psi",
                "sim/flightmodel/position/local_vx","sim/flightmodel/position/local_vy",
                "sim/flightmodel/position/local_vz","sim/flightmodel/position/local_ax",
                 "sim/flightmodel/position/local_ay","sim/flightmodel/position/local_az",
                 "sim/flightmodel/position/groundspeed","sim/flightmodel/position/indicated_airspeed",
                 "sim/flightmodel/position/indicated_airspeed2","sim/flightmodel/position/true_airspeed",
                "sim/flightmodel/position/M","sim/flightmodel/position/N","sim/flightmodel/position/L",
                 "sim/flightmodel/position/P","sim/flightmodel/position/Q","sim/flightmodel/position/R",
                 "sim/flightmodel/position/P_dot","sim/flightmodel/position/Q_dot","sim/flightmodel/position/R_dot",
                 "sim/flightmodel/position/Prad","sim/flightmodel/position/Qrad","sim/flightmodel/position/Rrad"]
        values = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.client.sendDREFs(drefs, values)
        #We start such that the front wheel is at the teleport location
        start_lat,start_lon=transform(lat,lon,heading+180.0,self.dist_to_front_wheel)
        # Reset position on runway at desired location (we add a meter to account for the distance above the ground of fuselage)
        self.client.sendPOSI([start_lat,start_lon,altitude+1.0,-998,-998,heading,1],0)

    	   # Repair any damage
        self.client.sendDREFs(["sim/operation/fix_all_systems"], [1])    

#This class implements the throttle controller
#The throttle controller may cause the engine to stall if stepping down velocity quickly 
#This could use some additional tuning, the caravan model engine seems quite sensitive 
class ThrottleController:
    def __init__(self,reference_speed=0.0):
        self.pid_throttle=PID(1.0,0.0,3.0)
        self.pid_throttle.setSampleTime(.01)
        self.reference_speed=reference_speed
        
    def compute_throttle(self,groundspeed,brakes):
        error=self.reference_speed-groundspeed

        self.pid_throttle.update(-error)
        #If we have brakes off apply throttle, otherwise do nothing, 
        #this prevents the throttle controller from fighting us if we want to stop
        if brakes==0.0:
            #Clip the throttle to ramp up gently
            throttle_input=np.clip(self.pid_throttle.output,-0.2,0.2)
        else:
            throttle_input=0.0
        return throttle_input
        
    def set_reference_speed(self,speed):
        self.reference_speed=speed
        
#This class implements the rudder controller        
class RudderController:
    def __init__(self,K):
        #K is a tuning parameter for the controller
        self.K=K
        self.target_lat_start=0.0
        self.target_lon_start=0.0
        self.target_lat_end=0.0
        self.target_lon_end=0.0

    #Set a target line segment    
    def set_target(self,point1,point2):
        self.target_lat_start=point1[0]
        self.target_lon_start=point1[1]
        self.target_lat_end=point2[0]
        self.target_lon_end=point2[1]
     
    #Compute the rudder control
    def compute_rudder(self,current_lat,current_lon,current_heading,current_velocity): 
        #Get the desired heading
        desired_heading=initial_bearing(self.target_lat_start,self.target_lon_start,self.target_lat_end,self.target_lon_end)
        #Compute the heading error with the proper sign
        heading_error=compute_heading_error(desired_heading,current_heading)*(np.pi/180)

        #Compute the cross track error
        cte=cross_track_distance(self.target_lat_start,self.target_lon_start,self.target_lat_end,self.target_lon_end,current_lat,current_lon)  
        
        #Apply the stanley control law
        #From http://isl.ecst.csuchico.edu/DOCS/darpa2005/DARPA%202005%20Stanley.pdf
        rudder_input=np.clip(heading_error+np.arctan2(self.K*cte,(current_velocity)),-1.0,1.0) 
        
        return rudder_input,cte
       
#This class keeps track of our trajectory
class Trajectory:
    def __init__(self,waypoints):  
        #List of desired waypoints
        self.waypoints=waypoints
        #The index of the current waypoint 
        self.current_waypoint=0
        #Have we completed the sequence
        self.complete=False
        #Is the closest waypoint the last one
        self.last_waypoint=False
        #The acceptable distance from the final point before we can stop
        self.completion_domain=1.0
        
    def update_waypoints(self,front_wheel_lat,front_wheel_lon,rear_wheel_lat,rear_wheel_lon):
        
        #Only do this computation if the current waypoint index is not the last waypoint
        if self.current_waypoint!=len(self.waypoints)-1:
            
            #This if statement protects from trajectories that are loops (recommend at least 200 sample points for circles)
            if self.current_waypoint==0:
                last_index=len(self.waypoints)-1
            else:
                last_index=len(self.waypoints)
                
            #Compute the distance to all waypoints    
            distances=[]  
            for waypoint in self.waypoints[0:last_index]:
                distances.append(great_circle_distance__haversine(front_wheel_lat,front_wheel_lon,waypoint[0],waypoint[1]))
                
            distances=np.array(distances)
            
            #Find the minimum distance index
            new_waypoint=np.argmin(distances)
    
            #If the new waypoint is greater in index than the current one it becomes the current one
            if new_waypoint>self.current_waypoint:
                self.current_waypoint=new_waypoint
        
        #If we have reached the end waypoint index and we are within some domain of it with the rear wheel we are done
        if self.current_waypoint==len(self.waypoints)-1 :
            self.last_waypoint=True
            rear_wheel_dist=great_circle_distance__haversine(rear_wheel_lat,rear_wheel_lon,
                                                             self.waypoints[self.current_waypoint][0],self.waypoints[self.current_waypoint][1])
            if rear_wheel_dist<self.completion_domain:
                self.complete=True
        
 

def run_trajectory(lat_interp,lon_interp,vel_interp,pts,start_altitude):
        
    #Construct the trajectory 
    waypoints=zip(lat_interp,lon_interp,vel_interp)
    traj=Trajectory(waypoints)
    
    #Initialize the state, reset the plane, create controllers and trajectory
    state=VehicleState()
    #Get the initial heading
    start_heading=initial_bearing(lat_interp[0],lon_interp[0],lat_interp[1],lon_interp[1])
    #Teleport the plane
    state.reset_plane(lat_interp[0],lon_interp[0],start_heading,start_altitude)
    #Set the brakes to off
    state.set_brake(0)
    throttle_ctrl=ThrottleController()
    rudder_ctrl=RudderController(K=0.5)
    while True:
        #Control the sample rate
        time.sleep(.01)
        #Get out new states
        state.update_state()
        #See if we have a new waypoint w.r.t the front wheel
        traj.update_waypoints(state.front_wheel_lat,state.front_wheel_lon,state.rear_wheel_lat,state.rear_wheel_lon)
        #If we are not done
        if traj.complete==False:
            #Set the reference speed
            throttle_ctrl.set_reference_speed(traj.waypoints[traj.current_waypoint][2])
            #Compute the throttle control
            throttle=throttle_ctrl.compute_throttle(state.groundspeed,state.brake)
            #Set the rudder controller target line segment
            #Check if we are at the last waypoint
            if traj.last_waypoint==False:
                rudder_ctrl.set_target(traj.waypoints[traj.current_waypoint],traj.waypoints[traj.current_waypoint+1])
            else:
                rudder_ctrl.set_target(traj.waypoints[traj.current_waypoint-1],traj.waypoints[traj.current_waypoint])
            #Compute the rudder control input
            rudder,cte=rudder_ctrl.compute_rudder(state.front_wheel_lat,state.front_wheel_lon,state.heading,state.groundspeed)
     
            #Send our control
            state.set_control(rudder,throttle)
                
        #We are done    
        else:
            #If we are done send zeros for the control and set the parking brake
            state.set_control(0,0) 
            state.set_brake(1)
            print('Trajectory Complete!')
            return 0
            


