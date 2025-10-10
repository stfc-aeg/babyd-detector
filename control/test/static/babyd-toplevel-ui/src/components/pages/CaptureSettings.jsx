import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { ToggleSwitch } from 'odin-react';
import { WithEndpoint } from 'odin-react';
import ButtonTitleCard from '../common/ButtonTitleCard';
import HeatmapPlotWithRange from '../common/HeatmapPlotWithRange';
import CaptureTable from '../common/CaptureTable';
import CaptureControlPanel from '../common/CaptureControlPanel';

const EndPointButton = WithEndpoint(Button);
const EndpointToggleSwitch = WithEndpoint(ToggleSwitch);

function CaptureSettings({ munirEndpoint }) {
  const captures = munirEndpoint?.data.munir?.captures || {};
  const coarse_data = munirEndpoint?.data?.liveview?.frame_data?.coarse || [];
  const overflow_data = munirEndpoint?.data?.liveview?.frame_data?.overflow || [];
  const fine_data = munirEndpoint?.data?.liveview?.frame_data?.fine || [];
  const built_data = munirEndpoint?.data?.liveview?.frame_data?.built || [];
  const isFrameBasedCapture = munirEndpoint?.data?.munir?.args?.frame_based_capture;
  const isDarkCorrecting = munirEndpoint?.data?.babyd?.liveview?.dark_correct_active;

  return (
    <ButtonTitleCard
      title="Capture Settings"
      actions={[
        <EndpointToggleSwitch
          key="frame-based"
          endpoint={munirEndpoint}
          event_type="click"
          label="Frame based capture"
          fullpath="munir/args/frame_based_capture"
          checked={isFrameBasedCapture}
          value={isFrameBasedCapture}
        />,
        <EndpointToggleSwitch
          key="dark-correction"
          endpoint={munirEndpoint}
          event_type="click"
          label="Dark correction"
          fullpath="liveview/dark_correct_active"
          checked={isDarkCorrecting}
          value={isDarkCorrecting}
        />,
        <EndPointButton
          key="capture-dark"
          endpoint={munirEndpoint}
          event_type="click"
          fullpath="liveview/dark_correct_capture"
          value={true}
          className="w-100"
          variant="secondary"
        >
          Capture Dark Data
        </EndPointButton>,
      ]}
    >
      <Container fluid>
        <Row>
          <Col sm={12} md={12} lg={12} xl={12} xxl={12}>
            <CaptureControlPanel
              munirEndpoint={munirEndpoint}
              isFrameBasedCapture={isFrameBasedCapture}
            />

            <Row style={{ paddingTop: '15px' }}>
              <Col sm={12}>
                <CaptureTable captures={captures} munirEndpoint={munirEndpoint} />
              </Col>
            </Row>
          </Col>

          <Col sm={12} md={12} lg={6} xl={6} xxl={3}>
            <HeatmapPlotWithRange
              data={fine_data}
              title="Fine Preview"
              initialMin={0}
              initialMax={128}
            />
          </Col>

          <Col sm={12} md={12} lg={6} xl={6} xxl={3}>
            <HeatmapPlotWithRange
              data={coarse_data}
              title="Coarse Preview"
              initialMin={0}
              initialMax={256}
            />
          </Col>

          <Col sm={12} md={12} lg={6} xl={6} xxl={3}>
            <HeatmapPlotWithRange
              data={overflow_data}
              title="Overflow Preview"
              initialMin={0}
              initialMax={1}
            />
          </Col>

          <Col sm={12} md={12} lg={6} xl={6} xxl={3}>
            <HeatmapPlotWithRange
              data={built_data}
              title="Built Preview"
              initialMin={0}
              initialMax={65536}
            />
          </Col>
        </Row>
      </Container>
    </ButtonTitleCard>
  );
}

export default CaptureSettings;