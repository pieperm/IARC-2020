"""
Takes information from the camera and gives it to vision
"""

import os
import sys

parent_dir = os.path.dirname(os.path.abspath(__file__))
gparent_dir = os.path.dirname(parent_dir)
ggparent_dir = os.path.dirname(gparent_dir)
sys.path += [parent_dir, gparent_dir, ggparent_dir]

import json
from multiprocessing import Queue
from queue import Empty

from vision.obstacle.obstacle_finder import ObstacleFinder
from vision.common.import_params import import_params


CAMERA_IDS = {
    'obstacle': '',
    'module': '',
    'peg': '',
}

class Pipeline:
    """
    This is a pipeline class that takes in a video, runs an obstacle detection algorithm,
    and updates the blobs to the environment class.

    Parameters
    -------------
    vision_communication: multiprocessing queue
        Interface to share vision information with flight.
    flight_communication: multiprocessing queue
        Interface to recieve flight state information from flight.
    camera: Camera
        Camera to pull image from.
    """
    PUT_TIMEOUT = 1  # Expected time for results to be irrelevant.

    def __init__(self, vision_communication, flight_communication, camera):
        ##
        self.vision_communication = vision_communication
        self.flight_communication = flight_communication

        self.camera = camera.__iter__()

        ##
        prefix = 'vision' if os.path.isdir("vision") else ''

        #
        config_filename = os.path.join(prefix, 'obstacle', 'config.json')

        with open(config_filename, 'r') as config_file:
            config = json.load(config_file)

        self.obstacle_finder = ObstacleFinder(params=import_params(config))

    def run(self, prev_state):
        """
        Process current camera frame.
        """
        ##
        try:
            state = self.flight_communication.get_nowait()
        except Empty:
            state = prev_state

        ##
        try:
            depth_image, color_image = self.camera.take_picture(CAMERA_IDS[state])
        except KeyError:
            depth_image, color_image = None, None

        ##
        bboxes = []

        if state == 'early_laps':
            bboxes = self.obstacle_finder.find(color_image, depth_image)
        else:
            pass  # raise AttributeError(f"Unrecognized state: {state}")

        ##
        for bbox in bboxes:
            self.vision_communication.put(bbox, self.PUT_TIMEOUT)

        # from vision.common.blob_plotter import plot_blobs
        # plot_blobs(self.obstacle_finder.keypoints, color_image)

        return state

def init_vision(vision_comm, flight_comm, video, runtime=100):
    """
    Alex, call this function - not run.
    """
    pipeline = Pipeline(vision_comm, flight_comm, video)

    prev_state = 'start'

    for _ in range(runtime):
        prev_state = pipeline.run(prev_state)


if __name__ == '__main__':
    from vision.camera.bag_file import BagFile

    vision_comm = Queue(100000)

    flight_comm = Queue()  # type('FlightCommunication', (object,), {'get_state': lambda: 'early_laps'})
    flight_comm.put('early_laps')

    video_file = sys.argv[1]
    video = BagFile(100, 100, 60, video_file)

    init_vision(vision_comm, flight_comm, video)

    from time import sleep
    sleep(1)

    vision_comm.close()
    flight_comm.close()
