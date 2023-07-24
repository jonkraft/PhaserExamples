clear; close all;
warning('off','MATLAB:system:ObsoleteSystemObjectMixin');

% Key Parameters
signal_freq = 10.145e9;  % this is the HB100 frequency
%signal_freq = findTxFrequency();
plutoURI = 'ip:192.168.2.1';
phaserURI = 'ip:phaser.local';
run_calibration = true;
use_calibration = true;

%% Run Calibration
if run_calibration == true
    CalibrationData = calibrationRoutine(signal_freq);
    finalcalweights = CalibrationData.CalibrationWeights.FinalCalibrationWeights;
    save("calibration_data.mat", "finalcalweights");
else
    if isfile("calibration_data.mat") == true
        load("calibration_data.mat", "finalcalweights");
    else
        use_calibration = false;
    end
end

%% Load the measured gain profiles
load('GainProfile.mat','subArray1_NormalizedGainProfile','subArray2_NormalizedGainProfile','gaincode'); 

% Setup the pluto
rx = setupPluto(plutoURI);

% Setup the phaser
bf = setupPhaser(rx,phaserURI,signal_freq);
bf.RxPowerDown(:) = 0;
bf.RxGain(:) = 127;

% Create the model of the phaser, which consists of 2 4-element subarrays    
nElements = 4;
subarrayModel = phased.ULA('NumElements',nElements,'ElementSpacing',bf.ElementSpacing);
nSubarrays = 2;
arrayModel = phased.ReplicatedSubarray("Subarray",subarrayModel,"GridSize",[1,nSubarrays],'SubarraySteering','Custom');

% Create the steering vector for the subarray and the main array
subarraySteer = phased.SteeringVector("SensorArray",subarrayModel,'NumPhaseShifterBits',7);
arraySteer = phased.SteeringVector("SensorArray",arrayModel);

% Set the analog and digital calibration weights. To see the uncalibrated
% array factor, all weights are set to 1.
if use_calibration == true
    % These will need to be set based on the calibration routine
    analogWeights = finalcalweights.AnalogWeights;
    digitalWeights = finalcalweights.DigitalWeights;
else
    % Weights all equal to 1 is an uncalibrated antenna
    analogWeights = ones(4,2);
    digitalWeights = ones(2,1);
end

%% Sweep the steering angle and capture data
steeringAngle = -90 : 90;
ArrayFactor = zeros(size(steeringAngle));
for ii = 1 : numel(steeringAngle)
    currentangle = steeringAngle(ii);

    % Get the steering weights for the subarray elements
    subarraysteerweights = subarraySteer(signal_freq,currentangle);
    adjustedsubarrayweights = subarraysteerweights .* analogWeights;

    % Get element phase from steering weights
    sub1weights = adjustedsubarrayweights(:,1);
    sub2weights = adjustedsubarrayweights(:,2);
    sub1phase = rad2deg(angle(sub1weights));
    sub2phase = rad2deg(angle(sub2weights));
    phases = [sub1phase',sub2phase'];
    phases = phases - phases(1);
    phases = wrapTo360(phases);

    % Get the element gain from steering weights
    sub1gain = mag2db(abs(sub1weights));
    sub2gain = mag2db(abs(sub2weights));
    calibGainCode = zeros(1,8);
    for nch = 1 : 4
        % Set gain codes for array 1
        xp = sub1gain(nch);
        if xp == -Inf
            calibGainCode(nch) = 0;
        else
            calibGainCode(nch) = round(interp1(subArray1_NormalizedGainProfile(:,nch),gaincode,xp));
        end
    
        % Set gain codes for array 2
        xp = sub2gain(nch);
        if xp == -Inf
            calibGainCode(nch+4) = 0;
        else
            calibGainCode(nch+4) = round(interp1(subArray2_NormalizedGainProfile(:,nch),gaincode,xp));
        end
        
        % Make sure the values of the gain code is always <= 127
        calibGainCode(calibGainCode>127 | isnan(calibGainCode)) = 127;
    end

    % Set element phase and gain
    bf.RxPhase(:) = phases;
    bf.RxGain(:) = calibGainCode;

    % Collect data
    bf.LatchRxSettings();
    receivedSig_HW = rx();

    % Get the steering weights for the digital channels, we need to flip
    % them before applying the steering vector because the receive data is
    % out of order
    flipdigitalweights = [digitalWeights(2);digitalWeights(1)];
    arraysteerweights = arraySteer(signal_freq,currentangle);
    adjustedarrayweights = arraysteerweights .* flipdigitalweights;
    adjustedarrayweights = [adjustedarrayweights(2);adjustedarrayweights(1)];

    % Apply the digital steering weights
    receivedSig_HW_sum = receivedSig_HW * conj(adjustedarrayweights);

    % Get the array factor
    receivedFFT = fft(receivedSig_HW_sum);
    ArrayFactor(ii) = (max(abs(receivedFFT)));
end

%% Compare the measured array factor and model
[~,ind] = max(ArrayFactor);
EmitterAz = steeringAngle(ind);
figure(101)
subarrayWeights = conj(subarraySteer(signal_freq,EmitterAz));
arrayWeights = arraySteer(signal_freq,EmitterAz);
pattern(arrayModel,signal_freq,-90:90,0,'CoordinateSystem', ...
    'Rectangular','Type','powerdb','ElementWeights',[subarrayWeights,subarrayWeights],'Weights',arrayWeights)
hold on;

% Plot the measured data and the model
plot(steeringAngle,mag2db(ArrayFactor./max(abs(ArrayFactor))))

%%
bf.release();
rx.release();