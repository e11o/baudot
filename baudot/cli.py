import sys
import getopt

from core import FileEncoder

def main(argv):
    try:                                
        opts, args = getopt.getopt(argv, "hi:o:s:t:",["help",
                                                      "input-file=",
                                                      "output-file=",
                                                      "source-encoding=",
                                                      "target-encoding="]) 
    except getopt.GetoptError:           
        usage()                          
        sys.exit(2)                     

    input_file = None
    output_file = None
    source_encoding = None
    target_encoding = None
    for opt, arg in opts:                
        if opt in ("-h", "--help"):      
            usage()                     
            sys.exit()                  
        elif opt in ("-i", "--input-file"):
            input_file = arg
        elif opt in ("-o", "--output-file"):
            output_file = arg
        elif opt in ("-s", "--source-encoding"):
            source_encoding = arg
        elif opt in ("-t", "--target-encoding"):
            target_encoding = arg
    encoder = FileEncoder()
    if source_encoding is None:
        source_encoding = encoder.detect_encoding(input_file)
    encoder.convert_encoding(input_file, output_file, target_encoding)

def usage():
    print '''Usage:
baudot -i <input-file> -o <output-file> [-s <source-encoding>] -t <target-encoding>
'''
    
if __name__ == "__main__":
    main(sys.argv[1:])
