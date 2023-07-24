function [amp] = helperGetAmplitude(signal)
    amp = max(abs(fft(signal)));
end