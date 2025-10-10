# babyd-top-level

Top level Adapter and React UI for the control of babyd and its subsystems

Installed with:

- cd/mkdir to a dir for this project eg cd ~/babyd_daq
- ~/babyd_daq$ export ADXDMA_ROOT=/aeg_sw/work/projects/alpha-data/adxdma-driver-linux-0.11.0/     (export ADXDMA_ROOT=/usr/local/alpha-data/adxdma-driver-linux-0.11.0/) for te7seneca
- ~/babyd_daq$ virtualenv babyd_3.9.5 (or suitable venv name)
- ~/babyd_daq$ source babyd_3.9.5/bin/activate 
- (babyd_3.9.5) ~/babyd_daq$ pip install versioneer
- (babyd_3.9.5) ~/babyd_daq$ pip install git+https://github.com/stfc-aeg/adxdma.git@main#subdirectory=control
- (babyd_3.9.5) ~/babyd_daq$ git clone https://github.com/stfc-aeg/babyd-detector.git
- (babyd_3.9.5) ~/babyd_daq$ cd babyd-detector/
- (babyd_3.9.5) ~/babyd_daq/babyd-detector$ git checkout control
- (babyd_3.9.5) ~/babyd_daq/babyd-detector$ cd control/
- (babyd_3.9.5) ~/babyd_daq/babyd-detector/control$ pip install .
- (babyd_3.9.5) ~/babyd_daq/babyd-detector/control$ 
