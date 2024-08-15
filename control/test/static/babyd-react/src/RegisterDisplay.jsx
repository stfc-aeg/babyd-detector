import React, { useEffect, useState } from 'react';

import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import Stack from 'react-bootstrap/Stack';
import Container from 'react-bootstrap/Container';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import Modal from 'react-bootstrap/Modal';


import {WithEndpoint, ToggleSwitch} from "odin-react";

import styles from './App.css'

const EndpointButton = WithEndpoint(Button);
const EndpointToggle = WithEndpoint(ToggleSwitch);
const EndpointInput = WithEndpoint(Form.Control);


export function RegisterDisplay(props) {

    const {register_name, register_data, readOnly=true, endpoint=null, fullpath=''} = props;

    const [data, changeData] = useState(register_data);

    const onChangeData = (event) => {
        console.log(event);
        // console.log(event.target.id);

        // var new_data = data;
        const index = parseInt(event.target.id);
        console.log(index);

        const new_data = data.map((c, i) => {
            if (i === index) {
                return parseInt(event.target.value, 16) || 0;
            } else {
                return c;
            }
        });
        console.log(new_data);

        changeData(new_data);
    }

    useEffect(() => {
        console.log("Register Data Changed for " + register_name);
        changeData(register_data);
    }, [register_data])

    return (
        <InputGroup>
            <InputGroup.Text>{register_name}</InputGroup.Text>
            {data.map(
                (data_word, index) => (
                    <Form.Control key={index.toString()} id={index.toString()} 
                    onChange={readOnly ? null : onChangeData}
                    value={"0x" + data_word.toString(16).toUpperCase()}
                    readOnly={readOnly}
                    disabled={readOnly}/>
                )
            )}
            {readOnly ? <></> : 
                <EndpointButton endpoint={endpoint} event_type='click' fullpath={fullpath} value={data}>
                    Update Register
                </EndpointButton>
            }
        </InputGroup>
    );

}

export function DetailedRegisterDisplay(props) {
    const {endpoint, name, addr, reg_data, fields=null, readOnly=false} = props;

    const [data, changeData] = useState(reg_data);

    const [model_show, setShow] = useState(false);

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const num_input_per_row = 4;

    const reshape_array = (input_list, cols) => {
        var matrix = [], i, k;
        for (i = 0, k = -1; i < input_list.length; i++)
        {
            if(i % cols === 0)
            {
                k++;
                matrix[k] = [];
            }

            matrix[k].push(input_list[i]);
        }


        return matrix;
    }

    useEffect(() => {
        console.log("Register Data Changed for " + name);
        changeData(reg_data);
    }, [reg_data]);

    const onChangeData = (event) => {
        console.log(event);
        // console.log(event.target.id);

        // var new_data = data;
        const index = parseInt(event.target.id);
        console.log(index);

        const new_data = data.map((c, i) => {
            if (i === index) {
                return parseInt(event.target.value, 16) || 0;
            } else {
                return c;
            }
        });
        console.log(new_data);

        changeData(new_data);
    }

    // const popover = (
    //     <Popover id={name + "_popover"} >
    //         <Popover.Header>Fields</Popover.Header>
    //         <Popover.Body>
    //             {fields ? Object.keys(fields).map((field, i) => (
    //                 <InputGroup>
    //                     <InputGroup.Text>{field}</InputGroup.Text>
    //                     <EndpointInput endpoint={endpoint} event_type="change"
    //                                    fullpath={name + "/fields/" + field}
    //                                    disabled={readOnly}/>
    //                 </InputGroup>
                
    //             )) : <></>}
    //         </Popover.Body>
    //     </Popover>
    //         )

    return (
        <>
        <Stack>
            <InputGroup>
                <Button onClick={handleShow} disabled={fields ? false : true}>{name}</Button>
                <Form.Control readOnly={true} disabled={true} value={"Addr: 0x" + addr?.toString(16).toUpperCase() || "0000"}/>
                <EndpointButton endpoint={endpoint} event_type='click' fullpath={name + "/value"} value={data}
                                disabled={readOnly}>
                    Update Register
                </EndpointButton>
            </InputGroup>
            <Container style={{ maxHeight: "95px", overflowY: "scroll", fontFamily: "monospace"}}>
            {data ? reshape_array(data, num_input_per_row).map(
            (selection, i) => (
                <InputGroup key={i}>
                    <InputGroup.Text id={i}>{(i*16).toString(16).toUpperCase()}</InputGroup.Text>
                    {selection.map((data_word, j) => (
                        <Form.Control key={(i*num_input_per_row + j).toString()}
                        id={(i*num_input_per_row + j).toString()}
                        value={data_word.toString(16).toUpperCase().padStart(8, "0")}
                        readOnly={readOnly}
                        disabled={readOnly}
                        onChange={onChangeData}/>
                    ))}
                </InputGroup>
            )
            ) : <></>}
            </Container>
            
        </Stack>
        {fields ? 
        <Modal show={model_show} onHide={handleClose}>
        <Modal.Header closeButton>
            <Modal.Title>{name} Fields</Modal.Title>
        </Modal.Header>
        <Modal.Body>
        {Object.keys(fields).map((field, i) => (
             <InputGroup>
                 <InputGroup.Text>{field}</InputGroup.Text>
                 <EndpointInput endpoint={endpoint} event_type="change"
                                fullpath={name + "/fields/" + field}
                                disabled={readOnly}
                                style={{textAlign: "right"}}
                                type="number"/>
             </InputGroup>
        ))}
        </Modal.Body>
    </Modal>
    : <></>}
    </>
    )

}
