class Node:
    def __init__(self,identifier,posx,force = 0,is_fixed=False):
        self.identifier = identifier
        self.force = force
        self.posx = posx
        self.is_fixed = is_fixed
        self.xdisplacement = None