import classicMonkeyTracking.histogram_match as hm
import dataAnalysis.helperFunctions.helper_functions as hf
import pandas as pd
import os, pdb

gammaValue = 0.75
equalizeFrame = True
nViews = 4
nStills = 5

startFrame = 900
overrideNFrames = 200

preprocAngles = [
    90,
    None,
    None,
    None
    ]

preprocRawVideo = False
if preprocRawVideo:
    preprocNames = [
        '201806031226-Proprio-Trial001-1',
        '201806031226-Proprio-Trial001-2',
        '201806031226-Proprio-Trial001-3',
        '201806031226-Proprio-Trial001-4',
        ]
    for idx, fileName in enumerate(preprocNames):
        hm.rotateAndCropVideo('./', fileName, angle = preprocAngles[idx], crop = None,
            outputFolder = 'cropped', startFrame = startFrame, overrideNFrames = overrideNFrames)

getTheStills = False
if getTheStills:
    hm.getNRandomStills(nStills, gammaValue = gammaValue, equalizeFrame = equalizeFrame)

    for i in range(nViews):
        hm.tileStills()

    input('Press ENTER to continue...')

tuneTheParameters = False
if tuneTheParameters:
    params = pd.DataFrame(0, index = range(nViews),
        columns = ['minVal', 'backProjThresh', 'mixingThresh', 'kernelRad'])
    for i in params.index:
        params.loc[i, 'minVal'], params.loc[i, 'backProjThresh'],\
        params.loc[i, 'mixingThresh'], params.loc[i, 'kernelRad'] =\
            hm.tuneParameters(gammaValue = gammaValue, equalizeFrame = equalizeFrame,
                initialDir = './', OutputType = hm.BACKPROJECTED_BACKPROJECTED_PLUS)
    params.to_csv('./params.csv')

runTheVideos = False
if runTheVideos:
    params = pd.read_csv('./params.csv')
    hm.batchBackProjectionToVideo(writeVideo = True, OutputType = hm.BACKPROJECTED_PLUS,
        gammaValue = gammaValue, equalizeFrame = equalizeFrame,
        preview = False, backProjThresh = params['backProjThresh'],
        convolutionKernelRadius = params['kernelRad'],
        mixingThresh = params['mixingThresh'],
        lowerValBound = params['minVal'])

extractTheTrainingData = True
if extractTheTrainingData:
    folderPath = './'
    cropWidth = None
    cropHeight = None
    nStills = 25
    fileInfos = [{
    'name' : '201806031226-Proprio-Trial001-1-rotated',
    'mustHaveJoints' : ["C_Right", "GT_Right", "K_Right","M_Right", "MT_Right"],
    'specificRange' : None,
    'crop' : (0,0,cropWidth, cropHeight)
    },{
    'name' : '201806031226-Proprio-Trial001-2-rotated',
    'mustHaveJoints' : ["C_Right", "GT_Right","M_Right", "MT_Right","C_Left"],
    'specificRange' : None,
    'crop' : (0,0,cropWidth, cropHeight)
    },{
    'name' : '201806031226-Proprio-Trial001-3-rotated',
    'mustHaveJoints' : ["C_Right", "GT_Right", "K_Right","M_Right", "MT_Right","C_Left"],
    'specificRange' : None,
    'crop' : (0,0,cropWidth, cropHeight)
    },{
    'name' : '201806031226-Proprio-Trial001-4-rotated',
    'mustHaveJoints' : ["GT_Right", "K_Right","M_Right", "MT_Right"],
    'specificRange' : None,
    'crop' : (0,0,cropWidth, cropHeight)
    }]

    for idx, fileInfo in enumerate(fileInfos):
        originX, originY, newWidth, newHeight = hm.getCropOrigin(folderPath, fileInfo['name'], cropWidth, cropHeight)
        fileInfo['crop'] = (originX, originY, newWidth, newHeight)
        hm.saveDeepLabCutTrainingData(folderPath,
            fileInfo, nStills = nStills, prevIdx = idx * nStills)
        pd.DataFrame(fileInfos).to_json(os.path.join(folderPath, 'training', 'training_params.json'))

preprocTestVideo = False
if preprocTestVideo:
    preprocNames = [
        '201806031226-Proprio-Trial001-1',
        '201806031226-Proprio-Trial001-2',
        '201806031226-Proprio-Trial001-3',
        '201806031226-Proprio-Trial001-4',
        ]
    params = pd.read_json('./training/training_params.json')

    from mpi4py import MPI
    COMM = MPI.COMM_WORLD
    SIZE = COMM.Get_size()
    RANK = COMM.Get_rank()

    #for idx, fileName in enumerate(preprocNames):
    hm.rotateAndCropVideo('./', preprocNames[RANK], angle = preprocAngles[RANK], crop = params.loc[RANK, 'crop'],
        outputFolder = 'cropped')
