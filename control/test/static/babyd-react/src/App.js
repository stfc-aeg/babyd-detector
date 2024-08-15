import React, { useEffect, useState } from 'react';

import 'odin-react/dist/index.css'

import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

import {OdinApp, TitleCard, WithEndpoint, StatusBox, ToggleSwitch, DropdownSelector} from 'odin-react';
import {useAdapterEndpoint} from 'odin-react';

import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import InputGroup from 'react-bootstrap/InputGroup';
import Accordion from 'react-bootstrap/Accordion';
import Dropdown from 'react-bootstrap/Dropdown';

import {RegisterDisplay, DetailedRegisterDisplay} from './RegisterDisplay';

const EndpointInput = WithEndpoint(Form.Control);
const EndpointButton = WithEndpoint(Button);
const EndpointCheck = WithEndpoint(Form.Check);
const EndpointDropdown = WithEndpoint(DropdownSelector);


function App() {

  const alphadata_endpoint = useAdapterEndpoint("basexdma/control", process.env.REACT_APP_ENDPOINT_URL);
  const udp_endpoint = useAdapterEndpoint("basexdma/registers/udp", process.env.REACT_APP_ENDPOINT_URL);
  const testapp_endpoint = useAdapterEndpoint("basexdma/registers/testapp", process.env.REACT_APP_ENDPOINT_URL);
  const i2c_endpoint = useAdapterEndpoint("basexdma/registers/iic", process.env.REACT_APP_ENDPOINT_URL);
  const auth_endpoint = useAdapterEndpoint("basexdma/registers/auth", process.env.REACT_APP_ENDPOINT_URL);
  const aurora_endpoint = useAdapterEndpoint("basexdma/registers/aurora", process.env.REACT_APP_ENDPOINT_URL);
  const framer_endpoint = useAdapterEndpoint("basexdma/registers/framer", process.env.REACT_APP_ENDPOINT_URL);

  const [ipLocal, changeIpLocal] = useState("");
  const [ipRemote, changeIpRemote] = useState("");

  const onChangeLocal = (event) => {
    changeIpLocal(event.target.value);
  }
  const onChangeRemote = (event) => {
    changeIpRemote(event.target.value);
  }

  const reg_columns = 2;

  useEffect(() => {
    console.log("Data Changed");
    if(alphadata_endpoint.data?.control?.ip_local){
      changeIpLocal(alphadata_endpoint.data.control.ip_local);
    }
    if(alphadata_endpoint.data?.control?.ip_remote){
      changeIpRemote(alphadata_endpoint.data.control.ip_remote);
    }
  }, [alphadata_endpoint.data.control?.ip_local, alphadata_endpoint.data.control?.ip_remote]);

  const reshape_register_array = (register_list, cols) => {
    var matrix = [], i, k;
    for(i = 0, k = -1; i< register_list.length; i++)
      {
        if( i % cols === 0)
        {
          k++;
          matrix[k] = [];
        }
        
        matrix[k].push(register_list[i]);
      }

      return matrix;
  }
  const get_sorted_register_list = (reg_object) => {
    let registers = Object.keys(reg_object).map((key) => {
      let obj = reg_object[key];
      obj.name = key;
      return obj;
      });

    registers = registers.sort(compare_reg);

    return registers;
  }

  const compare_reg = (a, b) => {
    let comp = 0;
      if(a.addr > b.addr){
        comp = 1;
      } else if (a.addr < b.addr) {
        comp = -1;
      }

      return comp;
  }

  // const register_filler = (width) => {
  //   let filler_list = [];
  //   for(let i = width; i < reg_columns; i ++)
  //   {
  //     filler_list.push((<Col></Col>));
  //   }
  //   return filler_list;
  // }

  const get_reg_list = (endpoint, reg_name) => {
    console.log("Getting register map for " + reg_name);
    return endpoint?.data[reg_name] ? reshape_register_array(get_sorted_register_list(endpoint.data[reg_name]), reg_columns).map(
      (selection, index) => 
        (
          <Row style={{margin: "5px"}}>
            {selection.map((register, index) => (
              <Col>
                <DetailedRegisterDisplay endpoint={endpoint}
                                         name={register?.name || "UNKNOWN"}
                                         addr={register?.addr || null}
                                         reg_data={register?.value || [0]}
                                         fields={register?.fields || null}
                                         readOnly={register?.readonly}/>
              </Col>
            ))}
          </Row>
        )
    ) : <></>;
  }

  const udp_reg_list = get_reg_list(udp_endpoint, 'udp');
  const testapp_reg_list = get_reg_list(testapp_endpoint, 'testapp');
  const i2c_reg_list = get_reg_list(i2c_endpoint, 'iic');
  const auth_reg_list = get_reg_list(auth_endpoint, 'auth');
  const aurora_reg_list = get_reg_list(aurora_endpoint, 'aurora');
  const framer_reg_list = get_reg_list(framer_endpoint, 'framer');

  return (
    <OdinApp title="BabyD ADXMDA Demo" navLinks={["Main Controls", "UDP", "Test App", "I2C", "Auth", "Aurora", "Framer"]}>
      <Container>
        <Row>
        <Col lg="3">
          <TitleCard title="Status">
            <Row>
            <Col>
              <ButtonGroup>
                <EndpointButton endpoint={alphadata_endpoint} event_type="click" fullpath="connect" value={true}>
                  Connect
                </EndpointButton>
                <EndpointButton endpoint={alphadata_endpoint} event_type="click" fullpath="disconnect" value={true}>
                  Disconnect
                </EndpointButton>
              </ButtonGroup>
            </Col>
            </Row>
            <Row>
            <Col>
              <StatusBox label="Alphadata" type={alphadata_endpoint.data?.control?.is_connected ? "success" : "danger"}>
                {alphadata_endpoint.data?.control?.is_connected ? "Connected" : "Disconnected"}
              </StatusBox>
            </Col>
            </Row>
          </TitleCard>
        </Col>
        <Col>
          <TitleCard title="Digest">
            <RegisterDisplay register_name="Digest" register_data={alphadata_endpoint.data?.control?.digest || [0]} 
                             readOnly={false} endpoint={alphadata_endpoint} fullpath="digest"/>
            {/* <RegisterDisplay register_name="DNA" register_data={alphadata_endpoint.data?.registers?.dna.value || [0]}
                             readOnly={true} />*/} {/*endpoint info only needed for writabele registers */}

          </TitleCard>
          <TitleCard title="IP Address">
            <Row>
            <Col>
              <InputGroup>
              <InputGroup.Text>Local IP Addr</InputGroup.Text>
              <Form.Control onChange={onChangeLocal} value={ipLocal}/>
              <EndpointButton endpoint={alphadata_endpoint} event_type='click' fullpath="ip_local" value={ipLocal}>
                Edit
              </EndpointButton>
              </InputGroup>
            </Col>
            <Col>
              <InputGroup>
              <InputGroup.Text>Remote IP Addr</InputGroup.Text>
              <Form.Control onChange={onChangeRemote} value={ipRemote}/>
              <EndpointButton endpoint={alphadata_endpoint} event_type='click' fullpath="ip_remote" value={ipRemote}>
                Edit
              </EndpointButton>
              </InputGroup>
            </Col>
            </Row>
          </TitleCard>
          <TitleCard title="Clock Speed">
              {/* <ButtonGroup>
                <EndpointButton endpoint={alphadata_endpoint} event_type="click" fullpath="data_rate" value={14}
                                variant={alphadata_endpoint.data?.data_rate === 14 ? "success" : "secondary"}>
                  {alphadata_endpoint.data?.data_rate === 14 ? <i class="bi bi-check-lg"></i> : <></>}
                  14 Gbps
                </EndpointButton>
                <EndpointButton endpoint={alphadata_endpoint} event_type="click" fullpath="data_rate" value={7}
                                variant={alphadata_endpoint.data?.data_rate === 7 ? "success" : "secondary"}>
                  {alphadata_endpoint.data?.data_rate === 7 ? <i class="bi bi-check-lg"></i> : <></>}
                  7 Gbps
                </EndpointButton>
              </ButtonGroup> */}
              <EndpointDropdown endpoint={alphadata_endpoint} event_type="select" fullpath="clock_speed/speed"
                                buttonText={alphadata_endpoint.data?.control?.clock_speed.speed || "Unknown"}>

                {alphadata_endpoint.data?.control?.clock_speed.options ? alphadata_endpoint.data.control.clock_speed.options.map(
                  (selection, index) => (
                    <Dropdown.Item eventKey={selection} key={index}>{selection}</Dropdown.Item>
                  )
                ) : <></>}
              </EndpointDropdown>
          </TitleCard>
        </Col>
        </Row>
      </Container>
      <Container>{udp_reg_list}</Container>
      <Container>{testapp_reg_list}</Container>
      <Container>{i2c_reg_list}</Container>
      <Container>{auth_reg_list}</Container>
      <Container>{aurora_reg_list}</Container>
      <Container>{framer_reg_list}</Container>
    </OdinApp>
  );
}

export default App;
