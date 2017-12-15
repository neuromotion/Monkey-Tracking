writer=VideoWriter('201710091108-Freely_Moving_Recording_IR_30min');
IRFramesPath='X:\group\Starbuck_Bilateral_Recordings\201710091108-Freely_Moving_Recording\split_starbuck_movie';
open(writer);

% filter
h=fspecial('laplacian');

for iFrame=1:54000
% for iFrame=1060:1060
    disp(iFrame)
    
    %load in IR frame mat file
    filePath=[IRFramesPath '201710091108-Freely_Moving_Recording\IRFrame' sprintf('%04d',iFrame) '.mat'];
    tmp=load(filePath);

    %Get the data from the mat file and do gamma processing
    varName=fieldnames(tmp);
    processed_frame=abs(17*imfilter(double(tmp.(varName{1}))'/65535,h).^1.5);
    
%     if any(any(imag(processed_frame)~=0))
%         warning(['Complex values at frame ' num2str(iFrame)])
%     end
    
    processed_frame(processed_frame>1)=1;

    %save frame to video
    writeVideo(writer,processed_frame);
end
close(writer)