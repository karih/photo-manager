'use strict';

import React, {Component} from "react";
import ReactDOM from 'react-dom';

import {App} from './app.js';
import './style.css';

console.log("rass", App);

export default (ReactDOM.render(React.createElement(App, null), document.getElementById('app')));
