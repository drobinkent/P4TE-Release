




class CP:
    def __init__(self):
        pass


class DPMemory:
    def __init__(self, length):
        self.stateful_memories = []
        for i in range(0,length+1):
            #Initializing all locations with zero
            self.stateful_memories.append(0)



class DPTcam:
python tcam simulations

assume 4 bit
1111

1000  1xxx
0100  x1xx
0010  xx1x
0001  xxx1


In our system we need to think about only one bit that is not don;t care. so no need to think generic tcam implementation

just assume

a prefix value in bytearray , a location indicating the 1 in mask. priority and another value for representing our action

we can easily generate the previous patterns and enter them in te tcam

for matching when a bytearray (which will be our bitmask) comes
    it simple read the highest priority value (prefix, mask...) in our tcam table. then take a n bit array with 0. then take 1 and shift it "mask "
times. then and with the prefix of the row. if it is 1 then this is a match. highest prioirty.

for lowest priority, simple read from opposite.

    now to search a specific range . we need to set correspoding locationi nthe bitmask. all other bits are 0. a function will search for the
    index of the 1 bit. that will be the mask value. and for searching use previous mechanism.

if the table is not hit use the lowest or highest prioty as the

    now assume we have 4 levels. so 4 bit bitmask. Now we want to find the matchinf enry forom level 3. so bitmask to be searched will be
0010. we search this in the table. iuf not found in the table then we can use highest prioty or lowest priority.
or even through another metadata field we can select logoc about which order to take. done. extra feature