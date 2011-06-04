import sys
import getopt
import os.path
import shutil

from core import CharsetConverter

def main(argv):
    try:                                
        opts, args = getopt.getopt(argv, "hi:o:s:t:",["help",
                                                      "input-file=",
                                                      "output-file=",
                                                      "source-encoding=",
                                                      "target-encoding=",
                                                      "no-backup"]) 
    except getopt.GetoptError:           
        usage()                          
        sys.exit(2)                     

    input_file = None
    output_file = None
    source_encoding = None
    target_encoding = None
    create_backup = True

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
        elif opt == "--no-backup":
            create_backup = False
    if input_file is None or target_encoding is None:
        print "ERROR: missing argument in command line\n"
        usage()
        sys.exit(2)
    if output_file is None:
        output_file = input_file
    if not os.path.exists(input_file):
        print "ERROR: input file does not exist"
        sys.exit(2)
    converter = CharsetConverter()
    if source_encoding is None:
        source_encoding = converter.detect_encoding(input_file)
        if source_encoding is None:
            print "ERROR: unable to detect source encoding"
            sys.exit(2)
    if source_encoding.lower() == target_encoding.lower():
        print "Skipping file %s - Source and target encodings are equal: %s" % (input_file, source_encoding)
        sys.exit()
    if os.path.exists(output_file):
        if os.path.isdir(output_file):
            print "ERROR: output file is a directory"
            sys.exit(2)
        if create_backup:
            shutil.copy(output_file, output_file + '~')
    converter.convert_encoding(input_file, output_file, target_encoding)

def usage():
    print '''Usage: baudot -i <input-file> -o <output-file> -t <target-encoding> [OPTIONS...]

OPTIONS:
-i, --input-file        File to convert
-o, --output-file       Destination file
-s, --source-encoding   Overwrite detected encoding
-t, --target-encoding   Encoding for the output file
--no-backup             Do not create backup file if output file exists
'''
