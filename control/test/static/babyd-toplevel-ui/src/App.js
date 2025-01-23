import './App.css';

import 'odin-react/dist/index.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import { Table, InputGroup, Dropdown, Card } from 'react-bootstrap';

import Alert from 'react-bootstrap/Alert';

import { TitleCard, ToggleSwitch, DropdownSelector, OdinApp, OdinGraph, StatusBox } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint } from 'odin-react';

const EndPointButton = WithEndpoint(Button);
const EndPointInput = WithEndpoint(Form.Control);
const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndpointToggleSwitch = WithEndpoint(ToggleSwitch)

function formatData(data, indentLevel = 0) {
  if (data == null) return ''; // Return empty string for null or undefined
  const indent = '    '; // 4 spaces for indentation
  let formattedData = '';

  Object.entries(data).forEach(([key, value]) => {
    const prefix = `${indent.repeat(indentLevel)}${key}: `;
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      formattedData += `${prefix}\n${formatData(value, indentLevel + 1)}`;
    } else if (Array.isArray(value)) {
      const arrayString = value.map(item => JSON.stringify(item)).join(', ');
      formattedData += `${prefix}[${arrayString}]\n`;
    } else {
      formattedData += `${prefix}${JSON.stringify(value)}\n`;
    }
  });

  return formattedData;
}



function WSStatusBox({ label, type = 'success', children }) {
  return (
    <Alert variant={type} style={{ whiteSpace: 'pre-wrap' }}>
      <div>{label ? `${label}: ` : ''}{children}</div>
    </Alert>
  );
}

function generateCoreInfo(adxdmaData) {
  // handle no data or nulld ata being passed to the function
  if (!adxdmaData) {
    return [];
  }

  // dynamically generate a list that counts how many frame_count sections are in the api response
  const numFrameCounts = Object.keys(adxdmaData).filter(key => key.startsWith('frame_count')).length;

  // create an array of components using the index from the numFrameCounts arrya
  return [...Array(numFrameCounts).keys()].map(index => {
    const frameCount = adxdmaData[`frame_count_${index}`];
    const linkStatus = adxdmaData[`link_status_${index}`];

    return (
      <Col sm={12} md={6} lg={6} xl={6} xxl={3} key={index}>
        <WSStatusBox label={`Core ${index}`}>
          {`\nFrame Count:\n${formatData(frameCount)}\nLink Status:\n${formatData(linkStatus)}`}
        </WSStatusBox>
      </Col>
    );
  });
}

function framesToSeconds(frames) {
  const FRAME_RATE = 533000;
  return Math.round(frames / FRAME_RATE);
}

function formatTime(totalSeconds) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  
  return [
    hours.toString().padStart(2, '0'),
    minutes.toString().padStart(2, '0'),
    seconds.toString().padStart(2, '0')
  ].join(':');
}

function ButtonTitleCard({ title, children, actions }) {
  return (
    // Return bootstrap card with margin-botton 4
    <Card className="mb-4">
      
      <Card.Header className="d-flex align-items-center">
        <span>{title}</span>
        <div className="ms-3 d-flex">
          {actions && actions.map((action, index) => (
            <div key={index} className="ms-2">
              {action}
            </div>
          ))}
        </div>
      </Card.Header>
      
      <Card.Body>
        {children}
      </Card.Body>
    </Card>
  );
}

function App() {
  const endpoint_url = process.env.NODE_ENV === 'development' ? process.env.REACT_APP_ENDPOINT_URL : window.location.origin;
  const munirEndpoint = useAdapterEndpoint('babyd', endpoint_url, 500);
  const LokiProxyEndpoint = useAdapterEndpoint('loki_proxy', endpoint_url, 500);

  const captures = munirEndpoint?.data.munir?.captures || {};
  const frame_data = munirEndpoint?.data?.liveview || [];
  const isADXDMAConnected = munirEndpoint?.data?.adxdma?.connected;
  const isLOKIConnected = munirEndpoint?.data?.loki?.connected;
  const isLOKIInitialised = munirEndpoint?.data?.loki?.initialised;
  const isFrameBasedCapture = munirEndpoint?.data?.munir?.args?.frame_based_capture;
  const isLokiBoardResponding = LokiProxyEndpoint?.data?.node_1 ? Object.keys(LokiProxyEndpoint.data.node_1).length > 0 : false;

   return (
    <OdinApp title="BabyD Top Level Control" navLinks={['Captures', 'LOKI', 'ADXDMA']}>
      <TitleCard title="Capture Settings">
        <Container fluid>
          <Row>
            <Col sm={12} md={12} lg={12} xl={12} xxl={7}>
              <Row>
                <Col sm={12} md={3} lg={3}>
                  <InputGroup>
                    <InputGroup.Text>File Path: </InputGroup.Text>
                    <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="munir/args/file_path" delay={3000}/>
                  </InputGroup>
                </Col>
                <Col sm={12} md={3} lg={3}>
                  <InputGroup>
                    <InputGroup.Text>File Name: </InputGroup.Text>
                    <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="munir/args/file_name" />
                  </InputGroup>
                </Col>
                <Col sm={12} md={3} lg={3}>
                  <InputGroup>
                    <InputGroup.Text>{isFrameBasedCapture ? 'Frames:' : 'Seconds:'} </InputGroup.Text>
                    <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="munir/args/num_intervals" />
                  </InputGroup> 
                </Col>
                <Col sm={12} md={3} lg={3}>
                  <InputGroup>
                    <InputGroup.Text>Delay: </InputGroup.Text>
                    <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="munir/args/delay" />
                  </InputGroup>
                </Col>
              </Row>
              <Row style={{ paddingTop: '15px' }}>
                <Col sm={12} md={4}>
                  <EndPointButton endpoint={munirEndpoint} event_type="click" fullpath="munir/stage_capture" value={true} className="w-100" variant="warning">
                    Stage Capture
                  </EndPointButton>
                </Col>
                <Col sm={12} md={4}>
                  <EndPointButton endpoint={munirEndpoint} event_type="click" fullpath="munir/execute" value={true} className="w-100" variant="success">
                    Execute Captures
                  </EndPointButton>
                </Col>
                <Col sm={12} md={4}>
                <EndpointToggleSwitch 
                endpoint={munirEndpoint} 
                event_type="click" 
                label="Frame based capture" 
                fullpath="munir/args/frame_based_capture" 
                checked={isFrameBasedCapture} 
                value={isFrameBasedCapture}>
              </EndpointToggleSwitch>
                </Col>
              </Row>

              <Row style={{ paddingTop: '15px' }}>
                <Col sm={12}>
                <Table striped bordered hover>
                  <thead>
                    <tr>
                      <th style={{ width: '10%' }}>Capture ID</th>
                      <th style={{ width: '30%' }}>File</th>
                      <th style={{ width: '10%' }}>Delays</th>
                      <th style={{ width: '15%' }}>Estimated Time</th>
                      <th style={{ width: '15%' }}>File Size</th>
                      <th style={{ width: '20%' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(captures).map((captureId) => {
                      const capture = captures[captureId];
                      const captureSeconds = framesToSeconds(capture.num_intervals);
                      const captureFileSizeGB = (capture.estimated_size_bytes / (1024 ** 3)).toFixed(2); // Convert to GB

                      return (
                        <tr key={captureId}>
                          <td>{capture.id}</td>
                          <td>{`${capture.file_path}${capture.file_name}`}</td>
                          <td>{formatTime(capture.delay)}</td>
                          <td>{formatTime(captureSeconds)}</td>
                          <td>{`${captureFileSizeGB} GB`}</td>
                          <td>
                            <div className="d-flex" style={{ gap: '8px' }}>
                              <EndPointButton
                                endpoint={munirEndpoint}
                                event_type="click"
                                fullpath="munir/duplicate_capture"
                                value={capture.id}
                                className="flex-grow-1"
                                variant="warning">
                                Duplicate
                              </EndPointButton>
                              <EndPointButton 
                                endpoint={munirEndpoint}
                                event_type="click"
                                fullpath="munir/remove_capture"
                                value={capture.id}
                                className="flex-grow-1"
                                variant="danger">
                                Remove
                              </EndPointButton>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                      <tr>
                        <td colSpan="3" className="text-end fw-bold">Total Capture Time:</td>
                        <td className="fw-bold">
                          {formatTime(
                            Object.values(captures).reduce((total, capture) => 
                              total + framesToSeconds(capture.num_intervals) + capture.delay, 0
                            )
                          )}
                        </td>
                        <td className="fw-bold">
                          {`${(
                            Object.values(captures).reduce((total, capture) => total + capture.estimated_size_bytes, 0) / (1024 ** 3)
                          ).toFixed(2)} GB`}
                        </td>
                        <td className="text-end fw-bold">
                          Free Space:{" "}
                          {munirEndpoint?.data?.munir?.free_space
                            ? `${(munirEndpoint?.data?.munir?.free_space / (1024 ** 3)).toFixed(2)} GB`
                            : "Unavailable"}
                        </td>
                      </tr>
                  </tbody>
                </Table>
                </Col>
              </Row>
            </Col>
            <Col sm={12} md={12} lg={12} xl={12} xxl={5}>
              <OdinGraph title='Built Live Frame Preview' type='heatmap' prop_data={frame_data} colorscale='viridis' width={500} height={500} ></OdinGraph>
            </Col>
          </Row>
        </Container>
      </TitleCard>


      <TitleCard title='Loki & BabyD Hardware'>
        <Row>
        <Col sm={12} md={6} lg={6} xl={6} xxl={6} >
          <TitleCard title='LOKI'>
            <Row>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
              <StatusBox label="Board Status">{isLokiBoardResponding ? 'Connected' : 'Disconnected'}</StatusBox>
              </Col>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
              <StatusBox label="CPU">{Math.round(LokiProxyEndpoint?.data?.node_1?.environment?.temperature?.zynq_ps) + " \u00b0C" }</StatusBox>

              </Col>
              <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
              <StatusBox label="Board">{Math.round(LokiProxyEndpoint?.data?.node_1?.environment?.temperature?.BOARD) + " \u00b0C" }</StatusBox>
              </Col>
            </Row>
          </TitleCard>
        
        </Col>

        <Col sm={12} md={6} lg={6} xl={6} xxl={6} >
          <TitleCard 
            title={ 
              <div className="ms-3 d-flex">
                <span>BabyD</span>
                
                <div className="ms-3 d-flex" style={{ gap: '15px' }}>
                  <EndPointButton
                    endpoint={munirEndpoint}
                    event_type="click"
                    fullpath="loki/connected"
                    value={!isLOKIConnected}
                    className="w-100"
                    style={{ whiteSpace: 'nowrap'}}
                    variant={isLOKIConnected ? 'danger' : 'success'}>
                    {isLOKIConnected ? 'Disconnect' : 'Connect'}
                  </EndPointButton>
                  <EndPointButton
                    endpoint={munirEndpoint}
                    event_type="click"
                    fullpath="loki/initialised"
                    value={!isLOKIInitialised}
                    className="w-100"
                    style={{ whiteSpace: 'nowrap'}}
                    variant={isLOKIInitialised ? 'danger' : 'success'}>
                    {isLOKIInitialised ? 'Re-Inititalise' : 'Inititalise'}
                  </EndPointButton>
                  <EndpointToggleSwitch 
                    endpoint={munirEndpoint} 
                    event_type="click" 
                    label="Manual SYNC" 
                    fullpath="loki/sync" 
                    checked={munirEndpoint.data.loki?.sync} 
                    value={munirEndpoint.data.loki?.sync}>
                  </EndpointToggleSwitch>
                </div>
              </div> }>
                <Row>
                  <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                    <StatusBox label="BabyD ASIC">{LokiProxyEndpoint?.data?.node_1?.application?.system_state?.ASIC_EN ? 'Enabled' : 'Disabled'}</StatusBox>
                  </Col>
                  <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                  <StatusBox label="BabyD Chip ">{LokiProxyEndpoint?.data?.node_1?.environment?.temperature?.BD_MIC_IN + " \u00b0C"}</StatusBox>
                  </Col>
                  <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                  </Col>
                </Row>
          </TitleCard>
        
        </Col>
        </Row>
      </TitleCard>
      {/* <TitleCard 
        title={
          <div className="d-flex align-items-center">
            <span style={{ fontSize: '1.5rem'}}>LOKI | </span>
            
            <div className="ms-3 d-flex" style={{ gap: '15px' }}>
              <EndPointButton
                endpoint={munirEndpoint}
                event_type="click"
                fullpath="loki/connected"
                value={!isLOKIConnected}
                className="w-100"
                variant={isLOKIConnected ? 'danger' : 'success'}>
                {isLOKIConnected ? 'Disconnect' : 'Connect'}
              </EndPointButton>
              <EndpointToggleSwitch 
                endpoint={munirEndpoint} 
                event_type="click" 
                label="Manual SYNC" 
                fullpath="loki/sync" 
                checked={munirEndpoint.data.loki?.sync} 
                value={munirEndpoint.data.loki?.sync}>
              </EndpointToggleSwitch>
            </div>
          </div>
        }>
      <Container fluid>
        <Row>
          <Col sm={12} md={6} lg={6} xl={6} xxl={6} >

          </Col>
          <Col sm={12} md={6} lg={6} xl={6} xxl={6} >
            <Card>
              <Card.Body>
                <Card.Title>
                  BabyD Status
                </Card.Title>
                <Card.Text>
                    <Row>
                      <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                      <StatusBox label="BabyD ASIC">{DirectLokiEndpoint.data.application?.system_state?.ASIC_EN ? 'Enabled' : 'Disabled'}</StatusBox>
                      </Col>
                      <Col sm={12} md={6} lg={4} xl={4} xxl={4}>

                      </Col>
                      <Col sm={12} md={6} lg={4} xl={4} xxl={4}>
                      </Col>
                    </Row>
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>

        </Row>






          <Row>

          </Row>
        </Container>
        
      </TitleCard> */}

      <ButtonTitleCard
        title="ADXDMA"
        actions={[
          <EndPointButton
            endpoint={munirEndpoint}
            event_type="click"
            fullpath="adxdma/connected"
            value={!isADXDMAConnected}
            className="w-100"
            variant={isADXDMAConnected ? 'danger' : 'success'}>
            {isADXDMAConnected ? 'Disconnect' : 'Connect'}
          </EndPointButton>
        ]}>
        <Container fluid>
          <Row>
            <Col sm={12} md={12} lg={12} xl={12} xxl={12}>
              <Row style={{ paddingBottom: '15px' }}>
                <Col sm={12} md={4} lg={4}>
                  <InputGroup>
                          <InputGroup.Text>Local IP Addr</InputGroup.Text>
                          <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="adxdma/ip_local" delay={3000} inputMode="text"/>
                  </InputGroup>
                </Col>
                <Col sm={12} md={4} lg={4}>
                  <InputGroup>
                          <InputGroup.Text>Remote IP Addr</InputGroup.Text>
                          <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="adxdma/ip_remote" delay={3000} inputMode="text"/>
                  </InputGroup>
                </Col>
                <Col sm={12} md={4} lg={4}>
                  <InputGroup>
                          <InputGroup.Text>Frames per event</InputGroup.Text>
                          <EndPointInput endpoint={munirEndpoint} event_type="change" fullpath="adxdma/trigger/frame_per_event" delay={3000}/>
                  </InputGroup>
                </Col>
              </Row>
              <Row>

                <Col sm={12} md={6} lg={3} xl={3} xxl={4} >
                  <InputGroup>
                    <InputGroup.Text>Trigger Mode</InputGroup.Text>
                    <EndpointDropdown endpoint={munirEndpoint} event_type="select" fullpath="adxdma/trigger/mode"
                                      buttonText={munirEndpoint.data.adxdma?.trigger.mode || "Unknown"}>
                      {munirEndpoint.data.adxdma?.trigger.available_modes ? 
                        munirEndpoint.data.adxdma.trigger.available_modes.map(
                          (selection, index) => (
                            <Dropdown.Item eventKey={selection} key={index}>{selection}</Dropdown.Item>
                          )
                        ): <></>}
                    </EndpointDropdown>
                  </InputGroup>
                </Col>
                <Col sm={12} md={6} lg={3} xl={3} xxl={4} > 
                  <InputGroup>
                          <InputGroup.Text>Clock Speed</InputGroup.Text>
                            <EndpointDropdown endpoint={munirEndpoint} event_type="select" fullpath="adxdma/clock_speed"
                                              buttonText={munirEndpoint.data.adxdma?.clock_speed || "Unknown"}>
                              {munirEndpoint.data.adxdma?.available_clock_speeds ? 
                                munirEndpoint.data.adxdma.available_clock_speeds.map(
                                  (selection, index) => (
                                    <Dropdown.Item eventKey={selection} key={index}>{selection}</Dropdown.Item>
                                  )
                                ): <></>}
                            </EndpointDropdown>
                          <InputGroup.Text>GHz</InputGroup.Text>
                  </InputGroup>
                </Col>
              </Row>

              {/* variant={isADXDMAConnected ? 'outline-danger' : 'outline-success'}> */}

              <Row style={{ paddingTop: '15px' }}>
                <Col sm={12}>
                {/* Table */}
                </Col>
              </Row>
            </Col>

          </Row>
          <Row>
              {generateCoreInfo(munirEndpoint.data?.adxdma)}

          </Row>
        </Container>
      </ButtonTitleCard>

      <TitleCard title="File Args">
        <Container fluid>
          <Row>
            <Col sm={12} md={12} lg={12} xl={12} xxl={6}>
              <Row>
                <Col sm={12} md={6} lg={4}>
                {/* textinput */}
                </Col>
                <Col sm={12} md={6} lg={4}>
                {/* textinput */}
                </Col>
                <Col sm={12} md={6} lg={4}>
                {/* textinput */}
                </Col>
              </Row>
              <Row style={{ paddingTop: '15px' }}>
                <Col sm={12} md={6}>
                {/* button */}
                </Col>
                <Col sm={12} md={6}>
                {/* button */}
                </Col>
              </Row>

              <Row style={{ paddingTop: '15px' }}>
                <Col sm={12}>
                {/* Table */}
                </Col>
              </Row>
            </Col>
            <Col sm={12} md={12} lg={12} xl={12} xxl={6}>
            {/* OdinGraph */}
            </Col>
          </Row>
        </Container>
      </TitleCard>
      
    </OdinApp>
  );
};

export default App;