#Sole task of this module is to call the resulr processor and that's all

import testAndMeasurement.ResultProcessor as rp
import sys


if __name__ == '__main__':
    if(len(sys.argv) <3):
        print("Need to pass 2 parameters: Iperf result Folder1, Iperf result folder 2")
    else:
        print("Parameters to result processor are: "+str(sys.argv))
        rp.compare2Resultfolder(sys.argv[1], sys.argv[2])

