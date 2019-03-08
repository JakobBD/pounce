from helpers.baseclass import BaseClass

class Level(BaseClass):
    subclasses = {}
    class_defaults={
        'cores_per_sample' : "NODEFAULT",
        'avg_walltime' : "NODEFAULT",
        'avg_walltime_postproc' : "NODEFAULT"
        }

