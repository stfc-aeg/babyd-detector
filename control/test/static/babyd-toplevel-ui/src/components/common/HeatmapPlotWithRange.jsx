import { useState } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import Plot from 'react-plotly.js';

function HeatmapPlotWithRange({ 
  data, 
  title, 
  initialMin = 0, 
  initialMax = 100,
  width = 400,
  height = 400 
}) {
  const [range, setRange] = useState({ min: initialMin, max: initialMax });

  return (
    <div>
      <Plot
        data={[
          {
            type: 'heatmap',
            z: data,
            colorscale: 'viridis',
            zmin: range.min,
            zmax: range.max,
          },
        ]}
        layout={{
          width: width,
          height: height,
          title: title,
          margin: { t: 30, b: 30, l: 30, r: 30 },
          yaxis: { scaleanchor: 'x', scaleratio: 1 },
        }}
      />
      <Form className="mt-2">
        <InputGroup size="sm">
          <InputGroup.Text>Range</InputGroup.Text>
          <Form.Control
            type="number"
            value={range.min}
            onChange={(e) => setRange({ ...range, min: Number(e.target.value) })}
            placeholder="Min"
          />
          <Form.Control
            type="number"
            value={range.max}
            onChange={(e) => setRange({ ...range, max: Number(e.target.value) })}
            placeholder="Max"
          />
        </InputGroup>
      </Form>
    </div>
  );
}

export default HeatmapPlotWithRange;