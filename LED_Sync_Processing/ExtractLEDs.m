function [ledStatus, intensities, regions, usedThreshs]=ExtractLEDs(videoFilename, nRegions, thresh, colorChannel, saveOutputVideo, prevDefRegions)
% [ledStatus, intensities, regions, usedThreshs]=extractLED(videoFilename, nRegions, thresh, colorChannel, saveOutputVideo, prevDefRegions)
% 
% Function which extracts from a video containing LEDs the frames where
% each LED was turned on or off.
% 
% 
% Outputs:
% ledStatus - NxM array of bools with N video frames by M LEDs/ROIs indicating
% whether each LED was on or not for each frame
% 
% intensities - NxM array of doubles which gives the average intensity of
% each ROI for each frame
% 
% regions - cell array of ROIs which correspond to each LED. Each cell
% contains the x,y coordinates, and width/height (in pixels) of the rectangle
% defining the ROI.
% 
% usedThreshs - the thresholds used for each ROI (useful if user
% got thresholds automatically)
% 
% 
% Inputs:
% videoFilename - string containing the file to be used
% 
% nRegions - number of LEDs/ROIs to extract
% 
% thresh - the ROI average intensity threshold to count the LED as on. Can
% be one value to use for all ROIs, or can be vector of values for each ROI.
% Can use 'auto' for the function to automatically calculate the best 
% threshold to use for each ROI.
% 
% colorChannel - which color channel to use for the intensity calculation.
% Can be 'red', 'blue', 'green', or 'grey'
% 
% saveOutputVideo - bool indicating if you want to save a video with the
% frames drawing region boxes whenever the LED status was detected to be
% on. Useful for verification but will take alot longer.
% 
% prevDefRegions(optional) - if you already defined ROIs from a previous
% call to this function and want to use the same one, use this input.
% Otherwise, the function will ask the user to select ROIs from the first
% frame of the video.
% 
% David Xing
% Last Updated 9/28/2017

% read in video
try
    vidReader = VideoReader(videoFilename);
catch
    error(['Cannot open ' videoFilename '!'])
end
nFrames = round(vidReader.Duration*vidReader.FrameRate);

% initialize output
ledStatus=zeros(nFrames,nRegions);

firstFrame = readFrame(vidReader);

% thickness (in pixels) to use for drawing region boxes
boxThickness=1;

% If the user did not input ROIs, ask user to define ROIs from first video
% frame
if (nargin==5)
    regions=cell(1,nRegions);
    image(firstFrame);

    firstFrameRects=firstFrame;
    %use getrect to let user select all regions
    for iROI=1:nRegions

        rect=round(getrect());
        %save to regions variable
        regions{iROI}=rect;
        
        %draw the selected rectangle on the frame so use can see what has
        %already been defined (use thickness of 2)
        firstFrameRects=AddRect(firstFrameRects,rect, boxThickness);
        
        %Display the image with newly defined region
        image(firstFrameRects);
        ylim([300 450]); xlim([100 350]);
        %display numbers of all the previously defined regions
        for iPrevROI=1:iROI
            text(regions{iPrevROI}(1)+regions{iPrevROI}(3)/2,regions{iPrevROI}(2)+regions{iPrevROI}(4)/2,...
                num2str(iPrevROI),'color',[1 1 1]);
        end 
        
    end
else
    %Otherwise, just display the first frame with the predefined ROI inputs
    if (length(prevDefRegions)~=nRegions)
        error('prevDefRegions must be of length nRegions!');
    end
    
    firstFrameRects=firstFrame;
    for iROI=1:nRegions
        rect=round(prevDefRegions{iROI});
        
        %draw rectangles around the regions
        firstFrameRects=AddRect(firstFrameRects,rect, boxThickness);
    end
    
    %draw frame
    image(firstFrameRects);
    
    %display numbers
    for iROI=1:nRegions
        rect=round(prevDefRegions{iROI});
        text(rect(1)+rect(3)/2,rect(2)+rect(4)/2, num2str(iROI),'color',[1 1 1]);
    end
    
    regions=prevDefRegions;
end

% Now that we have all our regions, go through all frames and get the
% average intensity in each region
intensities=zeros(nFrames, nRegions);

% first frame
firstFrameColor=GetFrameColorChannel(firstFrame,colorChannel);
for iRegion=1:nRegions
    ROI=firstFrameColor(regions{iRegion}(2):regions{iRegion}(2)+regions{iRegion}(4),...
        regions{iRegion}(1):regions{iRegion}(1)+regions{iRegion}(3));
    intensities(1,iRegion)=sum(ROI(:))/numel(ROI);
end

clear firstFrame firstFrameColor;

% all remaining frames
iFrame=2;
while hasFrame(vidReader)
    frame=readFrame(vidReader);
    frameColor=GetFrameColorChannel(frame,colorChannel);
    
    for iRegion=1:nRegions
        ROI=frameColor(regions{iRegion}(2):regions{iRegion}(2)+regions{iRegion}(4),...
            regions{iRegion}(1):regions{iRegion}(1)+regions{iRegion}(3));
        intensities(iFrame,iRegion)=sum(ROI(:))/numel(ROI);
    end
    
    disp(iFrame)
    iFrame = iFrame+1;
end

% if user wants to auto-calculate thresholds, look at the distribution of
% average intensities in each region and define a threshold based on
% mixture of gaussians model
if (strcmpi(class(thresh),'char') && strcmpi(thresh,'auto'))
    thresholds=zeros(1,nRegions);
    
    for iROI=1:nRegions
        %fit GM model
        try
            GMModel = fitgmdist(intensities(:,iROI),2);
        catch
            %mixture model failed, most likely due to there being only 1
            %distrbution (always on or always off), use average threshhold
            %from other ROIs in that case 
            warning(['Region ' num2str(iROI) ' failed to find GMModel, most likely LED is always off or always on, '...
                'will use average threshold of other ROIs as threshold value for this region.']);
            thresholds(iROI)=NaN;
            continue;
        end
        
        %find the middle between the two distributions using manahonobis
        %distance
        centerZScore=abs(diff(GMModel.mu))/sum(sqrt(squeeze(GMModel.Sigma)));
        
        if centerZScore<3
            warning(['Region ' num2str(iROI) ' has significant overlap, middle z score was ' num2str(centerZScore)...
                '. will use average threshold of other ROIs as threshold value for this region.']);
            thresholds(iROI)=NaN;
            continue;
        end
        
        [~,biggerGauss]=max(GMModel.mu);
        thresholds(iROI) = GMModel.mu(biggerGauss)-centerZScore*sqrt(GMModel.Sigma(1,1,biggerGauss));
        
    end
    
    %replace failed GM models with average thresholds
    if isnan(nanmean(thresholds))
        error('All defined LEDs are either always on or always off! Use manual threshold value')
    end
    thresholds(isnan(thresholds)) = nanmean(thresholds);
    
else
    
    %use defined threshold
    if (length(thresh)==1)
        thresholds=repmat(thresh,1,nRegions);
    elseif (length(thresh)~=nRegions)
        error('Number of thresholds must be equal to number of ROIs or be equal to 1!');
    else
        thresholds=thresh;
    end
    
end

% Now threshold for all intensities
ledStatus = intensities > repmat(thresholds,nFrames,1);
usedThreshs = thresholds;

% Finally, write output video file if user requested
if (saveOutputVideo)
    
    %name output video
    if(videoFilename(end-3)=='.')
        vidWriter=VideoWriter([videoFilename(1:end-4) '_processed'],'Motion JPEG AVI');
    else
        vidWriter=VideoWriter([videoFilename '_processed'],'Motion JPEG AVI');
    end
    vidWriter.FrameRate=vidReader.FrameRate;
    open(vidWriter);
    
    %load each frame of the video (again) and add boxes if LED is detected
    %to be on, then save the frame
    vidReader.CurrentTime=0;
    
    iFrame=1;
    while hasFrame(vidReader)
        
        frame=readFrame(vidReader);
        for iROI=1:nRegions
            
            if (ledStatus(iFrame,iROI))
                %draw rectangles around the regions
                rect=round(regions{iROI});
                frame=AddRect(frame, rect, boxThickness);
            end
            
        end
        
        writeVideo(vidWriter, frame);
        
        disp(iFrame);
        iFrame = iFrame+1;
        
    end
    
    close(vidWriter)
    
end

function outFrame=GetFrameColorChannel(inFrame,channel)
% from rgb image, get the specified channel

switch channel
    case 'red'
        outFrame=squeeze(inFrame(:,:,1));
    case 'blue'
        outFrame=squeeze(inFrame(:,:,1));
    case 'green'
        outFrame=squeeze(inFrame(:,:,1));
    case {'gray', 'grey'}
        outFrame=rgb2gray(inFrame);
end



function outFrame=AddRect(inFrame, rect, thichness)
% add a white rectangle to image

outFrame = inFrame;

outFrame(rect(2):rect(2)+rect(4),rect(1):rect(1)+thichness-1,:)=255;
outFrame(rect(2):rect(2)+thichness-1,rect(1):rect(1)+rect(3),:)=255;
outFrame(rect(2):rect(2)+rect(4),(rect(1)+rect(3)-thichness+1):(rect(1)+rect(3)),:)=255;
outFrame((rect(2)+rect(4)-thichness+1):(rect(2)+rect(4)),rect(1):rect(1)+rect(3),:)=255;


% 
