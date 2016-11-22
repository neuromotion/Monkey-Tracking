# RedBallTracker.py
import cv2, pdb, warnings, os, sys, enum, random
import numpy as np
from mpi4py import MPI
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib import pyplot as plt
from Tkinter import Tk
from tkFileDialog import askopenfilenames, askopenfilename, asksaveasfilename
from PIL import Image

NONE = 0
BACKPROJECTED = 1
ORIGINAL_BACKPROJECTED = 2
BACKPROJECTED_PLUS = 3
BACKPROJECTED_ALT = 4
THRESHOLDED_BACKPROJECTED = 5

COMM = MPI.COMM_WORLD
SIZE = COMM.Get_size()
RANK = COMM.Get_rank()

def getHSHistogram(templatePath, lowerValBound = 25, plotting = False):
    # get image which contains cutouts of the markers
    imgTemplate = cv2.imread(templatePath)
    imgTemplateHSV = cv2.cvtColor(imgTemplate,cv2.COLOR_BGR2HSV)

    # create a mask
    mask = np.zeros(imgTemplateHSV.shape[:2], np.bool)
    mask[imgTemplateHSV[:,:,2] > lowerValBound] = True
    #pdb.set_trace()

    maskedTemplateHSV = imgTemplateHSV[mask]
    maskedTemplateHSV = maskedTemplateHSV[:, np.newaxis, :]
    maskedTemplate = cv2.cvtColor(maskedTemplateHSV,cv2.COLOR_HSV2BGR)

    if plotting:
        cv2.namedWindow("Template", cv2.WINDOW_NORMAL)            # create windows, use WINDOW_AUTOSIZE for a fixed window size
        cv2.imshow("Template", maskedTemplate)

    templateHist =  cv2.calcHist([maskedTemplateHSV],[0, 1], None, [180, 256], [0, 180, 0, 256] )
    templateHist = cv2.GaussianBlur(templateHist, (9, 9), 0) # blur

    # normalize histogram
    cv2.normalize(templateHist,templateHist,0,255,cv2.NORM_MINMAX)
    if plotting:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = np.arange(0,256)
        y = np.arange(0,180)
        X, Y = np.meshgrid(x,y)

        surf = ax.plot_surface(X, Y, templateHist, rstride=1, cstride=1, cmap=cm.coolwarm,
            linewidth=.1, antialiased=True)
        plt.xlabel('Saturation')
        plt.ylabel('Hue')
        plt.show()

    #pdb.set_trace()
    return maskedTemplate, templateHist

def openVideo(filePath):
    capVideo = cv2.VideoCapture()                     # declare a VideoCapture object and associate to webcam, 0 => use 1st webcam
    #print("Attempting to open %s" % filePath)
    success = capVideo.open(filePath)

    if capVideo.isOpened() == False:            # check if VideoCapture object was associated to webcam successfully
        print "error: Video not accessed successfully\n\n"          # if not, print error message to std out
        os.system("pause")                                              # pause until user presses a key so user can see error message
        return                                                          # and exit function (which exits program)
    return capVideo

def getTupleOfFiles(filePath, defaultFile = ' ', message = "Please choose file(s)"):
    # get filename
    root = Tk()
    root.withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename_all = askopenfilenames(parent = root, title = message, initialdir = filePath) # open window to get file name

    if not filename_all: # if file not selected, select a default
        filename_all = (defaultFile,)
        warning_string = "No file selected, setting to default: %s" % filename_all[0]
        warnings.warn(warning_string, UserWarning, stacklevel=2)

    filename_root = filename_all[0].split(".")
    #pdb.set_trace()
    filename_path = '/'.join(filename_root[0].split('/')[:-1])+'/'

    return filename_all, filename_path

def tileStills(filePath = 'D:/Sensitive_Data'):
    filename_all, filename_path = getTupleOfFiles(filePath, message = "Which stills would you like to tile?")

    filename_root = filename_all[0].split('.')[:-1]
    cameraNo = filename_root[0].split('-')[-1][0]
    #pdb.set_trace()

    imgDummy = Image.open(filename_all[0])
    width, height = imgDummy.size
    nImages = len(filename_all)
    imgTile = Image.new('RGBA', (width, nImages*height))
    top = 0

    for filename in filename_all:
        imgCurrent = Image.open(filename)
        imgTile.paste(imgCurrent, (0, top))
        top += height
    imgTile.save(filename_path + "tiledTemplate-" + cameraNo + ".png")

def getNRandomStills(n = 10):
    filename_all, filename_path = getTupleOfFiles('D:/Sensitive_Data','D:/Sensitive_Data/201609191116-Boomer_Predox_Baseline_Treadmill/decrypt/201609191116-Boomer_Predox_Baseline_Treadmill_Ultraviolet_10-1.avi', message = "Which file would you like stills from?")

    capVideoDummy = openVideo(filename_all[0])

    nFrames = capVideoDummy.get(cv2.CAP_PROP_FRAME_COUNT)
    selection = [round(random.random()*nFrames) for i in range(n)]
    capVideoDummy.release()

    for filename in filename_all:
        filename_root = filename.split('.')[:-1]
        cameraNo = filename_root[0].split('-')[-1]
        #pdb.set_trace()
        capVideo = openVideo(filename)

        count = 0
        countSaved = 0
        while cv2.waitKey(1) != ord(' ') and capVideo.isOpened() and countSaved < n:  # until the Esc key is pressed or webcam connection is lost
            blnFrameReadSuccessfully, imgOriginal = capVideo.read()                   # read next frame
            if not blnFrameReadSuccessfully or imgOriginal is None:                   # if frame was not read successfully
                print "error: frame not read from webcam\n"                           # print error message to std out
                os.system("pause")                                                    # pause until user presses a key so user can see error message
                break                                                                 # exit while loop (which exits program)
            if count in selection:
                #pdb.set_trace()
                stillName = filename_root[0] + "_randomStill" + "%02d" % countSaved + ".png"
                cv2.imwrite(stillName, imgOriginal)
                countSaved += 1
            count += 1
        # end while
        capVideo.release()
    return

def getBackprojectedImg(imgOriginal, templateHist, backProjThresh = 50,
    openingKernelRadius = 3, closingKernelRadius = 3, dilationKernelRadius = 1,
    convolutionKernelRadius = 2):
    imgProcessed = cv2.cvtColor(imgOriginal,cv2.COLOR_BGR2HSV) # convert to hsv
    imgProcessed = cv2.calcBackProject([imgProcessed],[0,1],
        templateHist,[0,180,0,256],1)

    # Open image to remove small islands
    if openingKernelRadius > 1:
        imgProcessed = cv2.morphologyEx(imgProcessed, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
            (openingKernelRadius,openingKernelRadius)))

    if closingKernelRadius > 1:
        imgProcessed = cv2.morphologyEx(imgProcessed, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
            (closingKernelRadius,closingKernelRadius)))

    if dilationKernelRadius > 1:
        imgProcessed = cv2.morphologyEx(imgProcessed, cv2.MORPH_DILATE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
            (dilationKernelRadius,dilationKernelRadius)))

    if convolutionKernelRadius > 1:
        imgProcessed = cv2.filter2D(imgProcessed, -1,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
            (convolutionKernelRadius,convolutionKernelRadius)))

    # threshold and binary AND
    ret,imgMask1Ch = cv2.threshold(imgProcessed,backProjThresh,255,0)
    imgMask = cv2.merge((imgMask1Ch,imgMask1Ch,imgMask1Ch))

    imgThresholded = cv2.bitwise_and(imgOriginal,imgMask)
    imgProcessedThresholded = cv2.bitwise_and(imgProcessed,imgMask1Ch)

    return imgProcessedThresholded, imgProcessed, imgMask1Ch

def BackProjectionToVideo(filePath, templatePath, preview = False,
    DestinationPath = '', OutputType = NONE, overrideNFrames = 0):

    capVideo = openVideo(filePath)

    if DestinationPath:# Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        w=int(capVideo.get(cv2.CAP_PROP_FRAME_WIDTH ))
        h=int(capVideo.get(cv2.CAP_PROP_FRAME_HEIGHT ))
        fps=capVideo.get(cv2.CAP_PROP_FPS )
        if OutputType == BACKPROJECTED or OutputType == THRESHOLDED_BACKPROJECTED:
            out = cv2.VideoWriter(DestinationPath,fourcc, fps, (w,h), isColor=False)
        elif OutputType == ORIGINAL_BACKPROJECTED:
            out = cv2.VideoWriter(DestinationPath,fourcc, fps, (2*w,h), isColor=True)
            imgPlaceholder = np.zeros((h,2*w, 3), np.uint8)
        elif OutputType == BACKPROJECTED_PLUS or BACKPROJECTED_ALT:
            out = cv2.VideoWriter(DestinationPath,fourcc, fps, (w,h), isColor=True)
        if not(overrideNFrames):
            nFrames = capVideo.get(cv2.CAP_PROP_FRAME_COUNT)
        else:
            nFrames = overrideNFrames
    # get image which contains cutouts of the markers
    maskedTemplate, templateHist = getHSHistogram(templatePath, plotting = preview)

    if preview:
        cv2.namedWindow("Original", cv2.WINDOW_NORMAL)            # create windows, use WINDOW_AUTOSIZE for a fixed window size
        cv2.namedWindow("Processed", cv2.WINDOW_NORMAL)           # or use WINDOW_NORMAL to allow window resizing

    count = 0
    while cv2.waitKey(1) != ord(' ') and capVideo.isOpened() and count < nFrames:                # until the Esc key is pressed or webcam connection is lost
        blnFrameReadSuccessfully, imgOriginal = capVideo.read()            # read next frame

        if not blnFrameReadSuccessfully or imgOriginal is None:             # if frame was not read successfully
            print "error: frame not read from video stream\n"                     # print error message to std out
            #pdb.set_trace()
            #os.system("pause")                                              # pause until user presses a key so user can see error message
            break                                                           # exit while loop (which exits program)

        backProjThresh = 50

        if OutputType == THRESHOLDED_BACKPROJECTED:
            imgProcessed,_,_ = getBackprojectedImg(imgOriginal, templateHist, backProjThresh = backProjThresh)

        elif OutputType == BACKPROJECTED:
            _,imgProcessed,_ = getBackprojectedImg(imgOriginal, templateHist, backProjThresh = backProjThresh)

        elif OutputType == ORIGINAL_BACKPROJECTED:
            imgProcessedThresholded,_,_ = getBackprojectedImg(imgOriginal, templateHist, backProjThresh = backProjThresh)
            imgProcessedThresholded3ch = cv2.merge((imgProcessedThresholded,imgProcessedThresholded,imgProcessedThresholded))
            imgPlaceholder[:h, :w,:] = imgProcessedThresholded3ch
            imgPlaceholder[:h, w:2*w,:] = imgOriginal
            imgProcessed = imgPlaceholder

        elif OutputType == BACKPROJECTED_PLUS or BACKPROJECTED_ALT:
            imgProcessedThresholded, imgProcessed,_ = getBackprojectedImg(imgOriginal, templateHist, backProjThresh = backProjThresh)
            # threshold and binary AND
            _,imgMask1Ch = cv2.threshold(imgProcessed,backProjThresh,255,cv2.THRESH_BINARY_INV)

            # Open image to remove small islands
            openingKernelRadius = 5
            if openingKernelRadius > 1:
                imgMask1Ch = cv2.morphologyEx(imgMask1Ch, cv2.MORPH_OPEN,
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(openingKernelRadius,openingKernelRadius)))

            # Open image to remove small islands
            closingKernelRadius = 5
            if closingKernelRadius > 1:
                imgMask1Ch = cv2.morphologyEx(imgMask1Ch, cv2.MORPH_CLOSE,
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(closingKernelRadius,closingKernelRadius)))

            erosionKernelRadius = 50
            if erosionKernelRadius > 1:
                imgMask1Ch = cv2.morphologyEx(imgMask1Ch, cv2.MORPH_ERODE,
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(erosionKernelRadius,erosionKernelRadius)))

            convolutionKernelRadius = 1
            if convolutionKernelRadius > 1:
                imgMask1Ch = cv2.filter2D(imgMask1Ch, -1,
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(convolutionKernelRadius,convolutionKernelRadius)))

            imgMask = cv2.merge((imgMask1Ch,imgMask1Ch,imgMask1Ch))
            imgThresholded = cv2.bitwise_and(imgOriginal,imgMask)
            if OutputType == BACKPROJECTED_PLUS:
                imgProcessedThresholded3ch = cv2.merge((imgProcessedThresholded,imgProcessedThresholded,imgProcessedThresholded))
                imgProcessed = cv2.add(imgThresholded/3, imgProcessedThresholded3ch)
            elif OutputType == BACKPROJECTED_ALT:
                imgProcessed = cv2.merge((3*cv2.cvtColor(imgThresholded, cv2.COLOR_BGR2GRAY),np.zeros((h,w,1),np.uint8),imgProcessedThresholded))
                #pdb.set_trace()
        else:
            imgProcessed = getBackprojectedImg(imgOriginal, templateHist, backProjThresh = backProjThresh)

        if DestinationPath:
            sys.stdout.write("Process %d: Writing video. %d%%\r" % (RANK,int(count * 100 / nFrames+ 1)))
            sys.stdout.flush()
            count += 1
            out.write(imgProcessed)

        if preview:
            cv2.imshow("Original", imgOriginal)                 # show windows
            cv2.imshow("Processed", imgProcessed)
    # end while

    capVideo.release()
    if DestinationPath:
        out.release()
    cv2.destroyAllWindows()                     # remove windows from memory
    return

def batchBackProjectionToVideo(writeVideo = False, OutputType = BACKPROJECTED, overrideNFrames = 0):
    if RANK == 0:
        filename_all, filename_path = getTupleOfFiles('D:/Sensitive_Data', 'D:/Sensitive_Data/201609191116-Boomer_Predox_Baseline_Treadmill/decrypt/201609191116-Boomer_Predox_Baseline_Treadmill_Ultraviolet_10-1.avi', message = "Which video file(s) would you like to use?")
        templatename_all, templatename_path = getTupleOfFiles('D:/Sensitive_Data', 'D:/Sensitive_Data/201609191116-Boomer_Predox_Baseline_Treadmill/decrypt/tiledTemplate.png', message = "Which file would you like to use as template(s)?")

        destination_filename_all = []
        if writeVideo:
            for filePath in filename_all:
                # get filename
                root = Tk()
                root.withdraw() # we don't want a full GUI, so keep the root window from appearing
                filename_root = filePath.split(".")
                filename_processed = filename_root[0] + '-Processed.avi'
                filename = asksaveasfilename(parent = root, title = 'Please Name Processed file', initialfile = filename_processed) # open window to get file name
                destination_filename_all.append(filename)
    else:
        filename_all = None
        templatename_all = None
        destination_filename_all = None

    COMM.Barrier()  #sync MPI threads, waith for 0 to gather filenames before proceeding
    filename_all = COMM.bcast(filename_all, root = 0)
    templatename_all = COMM.bcast(templatename_all, root = 0)
    destination_filename_all = COMM.bcast(destination_filename_all, root = 0)

    #count = 0
    for i,filenames in enumerate(zip(filename_all,templatename_all, destination_filename_all)):
        if divmod(i, SIZE)[1] == RANK:
            print("Writing video %d of %d on process %d" % (i+1, len(filename_all),RANK))
            BackProjectionToVideo(filenames[0], filenames[1], preview = False,
            DestinationPath = filenames[2], OutputType = OutputType, overrideNFrames = overrideNFrames)

    #for filenames in zip(filename_all,templatename_all, destination_filename_all):
    #    print("Writing video %d of %d" % (count+1, len(filename_all)))
    #    BackProjectionToVideo(filenames[0], filenames[1], preview = False,
    #        DestinationPath = filenames[2], OutputType = OutputType, overrideNFrames = overrideNFrames)
    #    count += 1
###################################################################################################
if __name__ == "__main__":
    #getNRandomStills(20)
    #for i in range(7):
    #    tileStills()
    batchBackProjectionToVideo(writeVideo = True, OutputType = ORIGINAL_BACKPROJECTED, overrideNFrames = 2000)
