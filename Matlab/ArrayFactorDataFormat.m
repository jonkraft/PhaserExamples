classdef ArrayFactorDataFormat
    
    % Carry array factor data for calibration example
    
    properties
        SteeringAngle
        UncalibratedPattern
        AnalogCourseAmplitudeCalPattern
        AnalogPhaseCalPattern
        AnalogFineAmplitudeCalPattern
        DigitalAmplitudeCalPattern
        FullCalibration
    end

    methods
        function s = toStruct(this)
            s.SteeringAngle = this.SteeringAngle;
            s.UncalibratedPattern = this.UncalibratedPattern;
            s.AnalogCourseAmplitudeCalPattern = this.AnalogCourseAmplitudeCalPattern;
            s.AnalogPhaseCalPattern = this.AnalogPhaseCalPattern;
            s.AnalogFineAmplitudeCalPattern = this.AnalogFineAmplitudeCalPattern;
            s.DigitalAmplitudeCalPattern = this.DigitalAmplitudeCalPattern;
            s.FullCalibration = this.FullCalibration;
        end
    end
end

