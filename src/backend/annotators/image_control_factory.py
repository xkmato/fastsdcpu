class ImageControlFactory:
    def create_control(self, controlnet_type: str):
        if controlnet_type == "Canny":
            from backend.annotators.canny_control import CannyControl

            return CannyControl()
        elif controlnet_type == "Pose":
            from backend.annotators.pose_control import PoseControl

            return PoseControl()
        elif controlnet_type == "MLSD":
            from backend.annotators.mlsd_control import MlsdControl

            return MlsdControl()
        elif controlnet_type == "Depth":
            from backend.annotators.depth_control import DepthControl

            return DepthControl()
        elif controlnet_type == "LineArt":
            from backend.annotators.lineart_control import LineArtControl

            return LineArtControl()
        elif controlnet_type == "Shuffle":
            from backend.annotators.shuffle_control import ShuffleControl

            return ShuffleControl()
        elif controlnet_type == "NormalBAE":
            from backend.annotators.normal_control import NormalControl

            return NormalControl()
        elif controlnet_type == "SoftEdge":
            from backend.annotators.softedge_control import SoftEdgeControl

            return SoftEdgeControl()
        else:
            print("Error: Control type not implemented!")
            raise Exception("Error: Control type not implemented!")
