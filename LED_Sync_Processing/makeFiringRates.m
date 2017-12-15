clear;
load('201710091108-Freely_Moving_Recording-Array1480_Right-Trial001_First48ChanSpikes.mat');
load('KinectFrameTimes_30min.mat');

binSize=100;

for iFrame=1:length(frameTimes_Right)
    for iNeuron=1:length(timestamps)
        nSpikes=sum(timestamps{iNeuron}<frameTimes_Right(iFrame) & timestamps{iNeuron}>(frameTimes_Right(iFrame)-binSize));
        firingRates_Right(iNeuron, iFrame)=nSpikes/(binSize/1000);        
    end
end