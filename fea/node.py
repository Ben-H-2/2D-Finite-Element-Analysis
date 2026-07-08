class Node:
    def __init__(self,identifier,posx,posy=0.0,force_x=0.0,force_y=0.0,is_fixed_x=False,is_fixed_y=False):
        self.identifier = identifier
        self.posx = posx
        self.posy = posy
        self.force_x = force_x
        self.force_y = force_y
        self.is_fixed_x = is_fixed_x
        self.is_fixed_y = is_fixed_y
        self.x_displacement = 0.0
        self.y_displacement = 0.0