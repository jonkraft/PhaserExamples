function [rx,bf,phaserModel] = setupAntenna(fc_hb100)
    % Setup the Pluto, Phaser, and Phaser Model.
    
    % Setup the pluto
    plutoURI = 'ip:192.168.2.1';
    rx = setupPluto(plutoURI);

    % Setup the phaser
    phaserURI = 'ip:phaser.local';
    bf = setupPhaser(rx,phaserURI,fc_hb100);
    bf.RxPowerDown(:) = 0;
    bf.RxGain(:) = 127;
    
    % Create the model of the phaser    
    nElements = 4;
    nSubarrays = 2;
    subModel = phased.ULA('NumElements',nElements,'ElementSpacing',bf.ElementSpacing);
    phaserModel = phased.ReplicatedSubarray("Subarray",subModel,"GridSize",[1,nSubarrays]);
end