classdef CalibrationValueFormat
    
    % Store the antenna calibration values
    
    properties
        AnalogWeights
        DigitalWeights
    end
    
    methods
        function s = toStruct(this)
            s.AnalogWeights = this.AnalogWeights;
            s.DigitalWeights = this.DigitalWeights;
        end
    end
end

