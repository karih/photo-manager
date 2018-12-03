'use strict';

import React, {Component} from "react";
import ReactDOM from 'react-dom';

import {App} from './app.js';


import 'bootstrap/dist/css/bootstrap.min.css';
import './style.css';

export default (ReactDOM.render(React.createElement(App, null), document.getElementById('app')));
