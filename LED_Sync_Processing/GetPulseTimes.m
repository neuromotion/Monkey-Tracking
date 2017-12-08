% taking NS5 Data and finding the time of LED pulses to sync to kinect

clear;

% load in frame pulse numbers
load('30Min_Sync_Results.mat')


% threshold for detecting rising edges
thresh=10000;

% I manually found when the first LED pulse was and also when the first
% Simi pulse was on the left-side NSP and right-side NSP
ledStartTime_Left=1505353;
simiStartTime_Left=392313;

simiStartTime_Right=441034;
rightShift=simiStartTime_Right-simiStartTime_Left;

% chan 97 had the LED pulses
LEDchannel=97;
pulseTimes=[];

for iSample=1:1
    
    openNSx('../201710091108-Freely_Moving_Recording-Array1514_Left-Trial001.ns5',...
        ['c:' num2str(LEDchannel) ':' num2str(LEDchannel)],...
        ['t:' num2str(0) ':' num2str(252000000)] ,'sample')
    
    %get index of rising edges
    sig = NS5.Data(1,:);
    risingEdges=find(sig(3:end) >= thresh & sig(2:end-1) < thresh & sig(1:end-2) < thresh)+2;
    risingEdges(risingEdges<ledStartTime_Left)=[];
    pulseTimes=[pulseTimes risingEdges/30+(iSample-9000000)];
end

nanInds=isnan(framePulseMean);
framePulseMean(nanInds)=1;

frameTimes_Left=(risingEdges(round(framePulseMean)))/30;
frameTimes_Right=(risingEdges(round(framePulseMean))+rightShift)/30;
frameTimes_Left(nanInds)=nan;
frameTimes_Right(nanInds)=nan;