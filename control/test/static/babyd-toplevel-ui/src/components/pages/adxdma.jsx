import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { InputGroup, Dropdown } from 'react-bootstrap';
import { TitleCard, DropdownSelector } from 'odin-react';
import { WithEndpoint } from 'odin-react';
import CoreInfoDisplay from '../common/CoreInfoDisplay';

const EndPointButton = WithEndpoint(Button);
const EndPointInput = WithEndpoint(Form.Control);
const EndpointDropdown = WithEndpoint(DropdownSelector);

function ADXDMA({ munirEndpoint }) {
  const isADXDMAConnected = munirEndpoint?.data?.adxdma?.connected;

  return (
    <TitleCard
      title={
        <div className="d-flex align-items-center">
          <span>ADXDMA</span>
          <div className="ms-3 d-flex" style={{ gap: '15px' }}>
            <EndPointButton
              endpoint={munirEndpoint}
              event_type="click"
              fullpath="adxdma/connected"
              value={!isADXDMAConnected}
              className="w-100"
              variant={isADXDMAConnected ? 'danger' : 'success'}
            >
              {isADXDMAConnected ? 'Disconnect' : 'Connect'}
            </EndPointButton>
          </div>
        </div>
      }
    >
      <Container fluid>
        <Row>
          <Col sm={12} md={12} lg={12} xl={12} xxl={12}>
            <Row style={{ paddingBottom: '15px' }}>
              <Col sm={12} md={4} lg={4}>
                <InputGroup>
                  <InputGroup.Text>Local IP Addr</InputGroup.Text>
                  <EndPointInput
                    endpoint={munirEndpoint}
                    event_type="change"
                    fullpath="adxdma/ip_local"
                    delay={3000}
                    inputMode="text"
                  />
                </InputGroup>
              </Col>
              <Col sm={12} md={4} lg={4}>
                <InputGroup>
                  <InputGroup.Text>Remote IP Addr</InputGroup.Text>
                  <EndPointInput
                    endpoint={munirEndpoint}
                    event_type="change"
                    fullpath="adxdma/ip_remote"
                    delay={3000}
                    inputMode="text"
                  />
                </InputGroup>
              </Col>
              <Col sm={12} md={4} lg={4}>
                <InputGroup>
                  <InputGroup.Text>Frames per event</InputGroup.Text>
                  <EndPointInput
                    endpoint={munirEndpoint}
                    event_type="change"
                    fullpath="adxdma/trigger/frame_per_event"
                    delay={3000}
                  />
                </InputGroup>
              </Col>
            </Row>
            <Row>
              <Col sm={12} md={6} lg={3} xl={3} xxl={4}>
                <InputGroup>
                  <InputGroup.Text>Trigger Mode</InputGroup.Text>
                  <EndpointDropdown
                    endpoint={munirEndpoint}
                    event_type="select"
                    fullpath="adxdma/trigger/mode"
                    buttonText={munirEndpoint.data.adxdma?.trigger?.mode || 'Unknown'}
                  >
                    {munirEndpoint.data.adxdma?.trigger?.available_modes ? (
                      munirEndpoint.data.adxdma.trigger.available_modes.map(
                        (selection, index) => (
                          <Dropdown.Item eventKey={selection} key={index}>
                            {selection}
                          </Dropdown.Item>
                        )
                      )
                    ) : (
                      <></>
                    )}
                  </EndpointDropdown>
                </InputGroup>
              </Col>
              <Col sm={12} md={6} lg={3} xl={3} xxl={4}>
                <InputGroup>
                  <InputGroup.Text>Clock Speed</InputGroup.Text>
                  <EndpointDropdown
                    endpoint={munirEndpoint}
                    event_type="select"
                    fullpath="adxdma/clock_speed"
                    buttonText={munirEndpoint.data.adxdma?.clock_speed || 'Unknown'}
                  >
                    {munirEndpoint.data.adxdma?.available_clock_speeds ? (
                      munirEndpoint.data.adxdma.available_clock_speeds.map(
                        (selection, index) => (
                          <Dropdown.Item eventKey={selection} key={index}>
                            {selection}
                          </Dropdown.Item>
                        )
                      )
                    ) : (
                      <></>
                    )}
                  </EndpointDropdown>
                  <InputGroup.Text>GHz</InputGroup.Text>
                </InputGroup>
              </Col>
            </Row>

            <Row style={{ paddingTop: '15px' }}>
              <Col sm={12}>{/* Table placeholder */}</Col>
            </Row>
          </Col>
        </Row>
        <Row>
          <CoreInfoDisplay adxdmaData={munirEndpoint.data?.adxdma} />
        </Row>
      </Container>
    </TitleCard>
  );
}

export default ADXDMA;