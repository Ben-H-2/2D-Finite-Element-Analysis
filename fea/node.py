class Node:
    def __init__(self,identifier,posx,is_fixed=False):
        self.identifier = identifier
        self.posx = posx
        self.is_fixed = is_fixed
        self.xdisplacement = None