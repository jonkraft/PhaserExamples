function phase = helperGetPhase(signal)
    fsig = fft(signal);
    [~,ampidx] = max(fsig);
    phase = zeros(1,numel(ampidx));
    for i = 1:numel(ampidx)
        phase(i) = rad2deg(angle(fsig(ampidx(i),i)));
    end
end