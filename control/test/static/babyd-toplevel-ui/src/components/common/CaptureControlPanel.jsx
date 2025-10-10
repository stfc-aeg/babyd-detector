import { Row, Col, InputGroup } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { WithEndpoint } from 'odin-react';

const EndPointInput = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function CaptureControlPanel({ munirEndpoint, isFrameBasedCapture }) {
  return (
    <>
      <Row>
        <Col sm={12} md={3} lg={3}>
          <InputGroup>
            <InputGroup.Text>File Path: </InputGroup.Text>
            <EndPointInput
              endpoint={munirEndpoint}
              event_type="change"
              fullpath="munir/args/file_path"
              delay={3000}
            />
          </InputGroup>
        </Col>
        <Col sm={12} md={3} lg={3}>
          <InputGroup>
            <InputGroup.Text>File Name: </InputGroup.Text>
            <EndPointInput
              endpoint={munirEndpoint}
              event_type="change"
              fullpath="munir/args/file_name"
            />
          </InputGroup>
        </Col>
        <Col sm={12} md={3} lg={3}>
          <InputGroup>
            <InputGroup.Text>
              {isFrameBasedCapture ? 'Frames:' : 'Seconds:'}{' '}
            </InputGroup.Text>
            <EndPointInput
              endpoint={munirEndpoint}
              event_type="change"
              fullpath="munir/args/num_intervals"
            />
          </InputGroup>
        </Col>
        <Col sm={12} md={3} lg={3}>
          <InputGroup>
            <InputGroup.Text>Delay: </InputGroup.Text>
            <EndPointInput
              endpoint={munirEndpoint}
              event_type="change"
              fullpath="munir/args/delay"
            />
          </InputGroup>
        </Col>
      </Row>

      <Row
        style={{
          paddingTop: '15px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Col sm={12} md={4}>
          <EndPointButton
            endpoint={munirEndpoint}
            event_type="click"
            fullpath="munir/stage_capture"
            value={true}
            className="w-100"
            variant="secondary"
          >
            Stage Capture
          </EndPointButton>
        </Col>
        <Col sm={12} md={4}>
          <EndPointButton
            endpoint={munirEndpoint}
            event_type="click"
            fullpath="munir/execute"
            value={true}
            className="w-100"
            variant="success"
          >
            Execute Captures
          </EndPointButton>
        </Col>
      </Row>
    </>
  );
}

export default CaptureControlPanel;