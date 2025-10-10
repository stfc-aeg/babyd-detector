import { Table } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import { WithEndpoint } from 'odin-react';
import { framesToSeconds, formatTime } from '../functions/utils';

const EndPointButton = WithEndpoint(Button);

function CaptureTable({ captures, munirEndpoint }) {
  return (
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
          const captureFileSizeGB = (capture.estimated_size_bytes / 1024 ** 3).toFixed(2);

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
                    variant="warning"
                  >
                    Duplicate
                  </EndPointButton>
                  <EndPointButton
                    endpoint={munirEndpoint}
                    event_type="click"
                    fullpath="munir/remove_capture"
                    value={capture.id}
                    className="flex-grow-1"
                    variant="danger"
                  >
                    Remove
                  </EndPointButton>
                </div>
              </td>
            </tr>
          );
        })}
        <tr>
          <td colSpan="3" className="text-end fw-bold">
            Total Capture Time:
          </td>
          <td className="fw-bold">
            {formatTime(
              Object.values(captures).reduce(
                (total, capture) =>
                  total + framesToSeconds(capture.num_intervals) + capture.delay,
                0
              )
            )}
          </td>
          <td className="fw-bold">
            {`${(
              Object.values(captures).reduce(
                (total, capture) => total + capture.estimated_size_bytes,
                0
              ) /
              1024 ** 3
            ).toFixed(2)} GB`}
          </td>
          <td className="text-end fw-bold">
            Free Space:{' '}
            {munirEndpoint?.data?.munir?.free_space
              ? `${(munirEndpoint?.data?.munir?.free_space / 1024 ** 3).toFixed(2)} GB`
              : 'Unavailable'}
          </td>
        </tr>
      </tbody>
    </Table>
  );
}

export default CaptureTable;