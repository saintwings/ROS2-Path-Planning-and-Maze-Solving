import rclpy 
import cv2 
from rclpy.node import Node 
from cv_bridge import CvBridge 
from sensor_msgs.msg import Image

from .bot_localization import bot_localizer
from .bot_mapping import maze_converter
from .bot_pathplanning import pathfinders

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from .bot_control import Control
import numpy as np
cv2.namedWindow("maze (Shortest Path + Car Loc)",cv2.WINDOW_FREERATIO)


class Video_get(Node):
  def __init__(self):
    super().__init__('video_subscriber')# node name
    ## Created a subscriber 
    self.subscriber = self.create_subscription(Image,'/camera/image_raw',self.process_data,10)
    self.bridge = CvBridge() # converting ros images to opencv data

    self.bot_localizer = bot_localizer()
    self.maze_converter = maze_converter()
    self.path_finder = pathfinders()
    self.control = Control()

    self.publisher = self.create_publisher(Twist, '/cmd_vel', 40)
    self.velocity = Twist()
    self.pose_subscriber = self.create_subscription(Odometry,'/odom',self.control.get_pose,10)


  def process_data(self, data):
    
    frame = self.bridge.imgmsg_to_cv2(data,'bgr8') # performing conversion
    
    # Saving frame to display roi's
    frame_disp = frame.copy()
    
    # Stage 1 => Localizing the Bot
    self.bot_localizer.localize_bot(frame,frame_disp)

    # Stage 2 => Converting maze (image) into maze (matrix)
    self.maze_converter.graphify(self.bot_localizer.extracted_maze,self.bot_localizer.unit_dim)
    
    # Stage 2b => Using fast path_finders to find shortest paths i.e (Dijisktra and A*)
    if not self.path_finder.shortestpath_found:
      self.path_finder.dijisktra(self.maze_converter.Graph, self.maze_converter.Graph.start,self.maze_converter.Graph.end,self.maze_converter)
      self.path_finder.a_star(self.maze_converter.Graph, self.maze_converter.Graph.start,self.maze_converter.Graph.end,self.maze_converter)

    #shortest_path = self.maze_converter.shortest_path
    shortest_path = self.path_finder.shortest_path
    
    print("Nodes Visited [Dijisktra V A-Star*] = [ {} V {} ]".format(self.path_finder.dijiktra_nodes_visited,self.path_finder.astar_nodes_visited))
    self.control.nav_path(self.bot_localizer.loc_car, shortest_path, self.maze_converter.img_shortest_path,self.publisher,self.velocity,self.bot_localizer,frame_disp)

    cv2.imshow("Maze (Live)", frame_disp) # displaying what is being recorded 
    cv2.waitKey(10)
  
  
def main(args=None):
  rclpy.init(args=args)
  image_subscriber = Video_get()
  rclpy.spin(image_subscriber)
  rclpy.shutdown()
  
if __name__ == '__main__':
  main()