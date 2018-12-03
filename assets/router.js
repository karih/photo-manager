'use strict';

import React, {Component} from "react";

import app from './index.js';


function cast(param, value) {
	var new_value = null;
	switch (param.type) {
		case "int": 
			new_value = Number.parseInt(value);
			if (isNaN(new_value))
				new_value = null;
			break;
		case "float": 
			new_value = Number.parseFloat(value);
			if (isNaN(new_value))
				new_value = null;
			break;
		case "string":
			new_value = value;
			break
		default:
			console.log("ERROR: Unknown parameter type", param, value);
			new_value = value;
	}

	return [new_value, new_value == null ? null : (new_value.toString() != value), new_value == param.default];
}

export class Link extends React.Component {
	onClick(event) {
		// if normal click -> don't let browser reload
		if (event.ctrlKey) { 
			// if ctrl-click -> don't make any local changes
		} else {
			event.preventDefault();
			app.onChangeState(this.props.newState);
			return false;
		}
	}

	newStateUrl() {
		return app.router.updateState({...this.props.newState, ...{url: true}})	
	}

	render() {
		//console.log(this.props, app);

		let props = {}
		for (let key in this.props) {
			if (['children', 'newState', ].indexOf(key) < 0)
				props[key] = JSON.parse(JSON.stringify(this.props[key]));
		}
		
		return (<a href={this.newStateUrl()} onClick={(x) => this.onClick(x)} {...props}>{this.props.children}</a>);
	}
}

export class Router {
	constructor(views, default_view) {
		this.views = views;
		this.default_view = default_view;
		this.view = null;
		this.params = {};
		this.args = {};
	}

	base_href() { return document.getElementsByTagName('base')[0].href; }

	all_params(view=null) {
		//console.log("all_params")
		if (view == null)
			view = this.views[this.view];
		else
			view = this.views[view];

		let params = {};
		while (true) {
			Object.entries(view.params).forEach(function ([key, val]) {
				if (!params.hasOwnProperty(key)) {
					params[key] = val;
				}
			});

			if (view.hasOwnProperty("inherit"))
				view = this.views[view.inherit];
			else
				break;
		}

		return params;
	}

	read() {
		var pathname = window.location.href; // e.g. https://example.org/base_path/view/3?args 
		pathname = pathname.substr(0, pathname.length-window.location.search.length).replace(/\?$/, ""); // drop trailing ?args
		
		var view_path = pathname.substr(this.base_href().length); // drop leading .../base_path/
		//console.log("Read pathname", pathname, "vs base_href", this.base_href(), "view name", view_path);

		var found = false;
		let self = this;

		let patterns = {};
		patterns["int"] = '([0-9]+)';
		patterns["str"] = '([a-zA-Z]+)';
		
		for (let key in this.views) {
			let view = this.views[key];

			//console.log("Testing", key, ",", view.url, "==", view_path, "???")
	
			let url = view.url;
			let regex = /<[a-z]+:[a-z]+>/g;
			let matches = url.match(regex);
			let arg2pos = {};

			view.args = {};
			if (matches != null) {
				for (let i=0; i < matches.length; i++) {
					let type = null;
					let name = null;
					[type, name] = matches[i].replace("<", "").replace(">","").split(":");
					view.args[name] = {name: name, type: type, pattern: patterns[type]};
					url = url.replace("<" + type + ":" + name + ">", patterns[type]);
					arg2pos[name] = i+1;
					//console.log("Registering argument", name, "of type", type, "to view", key);
				}
			}

			url = new RegExp("^" + url + "$");
			//console.log("REGEXP", url, view_path)

			if (url.test(view_path)) {
				this.view = key;
				let match = url.exec(view_path);
				//console.log("REGEXP MATCH", match);

				Object.entries(view.args).forEach(function ([k, v]) {
					self.args[k] = cast(v, match[arg2pos[k]])[0];
				});

				//console.log("Setting view to ", key, "matching args", this.args);
				found = true; 
			}
		}

		if (!found)
			this.view = this.default_view;

		this.read_params();

		console.log("REPLACING STATE", this.state(), this.write_url());
		window.history.replaceState(this.state(), "", this.write_url());

		return this.state();
	}

	read_params() {
		var params = new URLSearchParams(window.location.search);
		//console.log("URL parameters", params.toString());
		this.params = {};

		let self = this;
		Object.entries(this.all_params()).forEach(function ([key, val]) {
			self.params[key] = val.default;
		});

		//console.log("Parameters initialized to default values", this.params);

		for (let pair of params) {
			let p = pair[0];
			let val = pair[1];
			if (this.all_params().hasOwnProperty(p)) {
				let ret = cast(this.all_params()[p], val);

				if (ret[0] == null) {
					//console.log("Removing param", p, "as it is null");
				} else if (ret[2]) {
					//console.log("Removing param", p, "as it is at default value");
				} else if (ret[1]) {
					//console.log("Rewriting param", p, "as it casted value does not match input");
					this.params[p] = ret[0];
				} else {
					//console.log("Param value valid", p, ret);
					this.params[p] = ret[0];
				}
			} else {
				//console.log("Param", p, "not valid for view.")
			}
		}
	}

	state() {
		return {view: this.view, args: this.args, params: this.params};
	}

	write_url(new_state=null) {
		if (new_state == null)
			new_state = this.state();
		//console.log("write_url()");
		let params = new URLSearchParams();
		
		Object.entries(this.nondefault_params(new_state.view, new_state.params)).forEach(function ([key, val]) {
			//console.log("Adding argument ", key, " value ", val);
			params.append(key, val);
		});

		let view_url = this.views[new_state.view].url;
		Object.entries(this.views[new_state.view].args).forEach(function ([key, val]) {
			//console.log("view_url was", view_url)
			view_url = view_url.replace("<" + val.type + ":" + val.name + ">", new_state.args[key]);
			//console.log("view_url is", view_url)
		});


		var url = this.base_href() + view_url + (params.toString().length > 0 ? "?" : "") + params.toString();
		//console.log("Suggested URL: ", url, "params", params.toString());

		return url;
	}

	nondefault_params(view=null, params=null) {
		let out = {};
		let all_params = (view == null) ? this.all_params() : this.all_params(view);
		let set_params = (params == null) ? this.params : params;
		Object.entries(all_params).forEach(function ([key, val]) {
			//console.log("nondefault_params()", "key", key, "val", val, "current value", self.params[key]);
			if (val.default != set_params[key])
				out[key] = set_params[key];
		});
		return out;
	}

	updateState(obj) {
		// TODO: Clean this up a bit - particularly how the object makes changes to itself before determining the url

		let self = this;
		let return_url = obj.hasOwnProperty("url") && obj.url;

		var old_state = {view: self.view, args: JSON.parse(JSON.stringify(self.args)), params: JSON.parse(JSON.stringify(self.params))};
		var new_state = {view: self.view, args: JSON.parse(JSON.stringify(self.args)), params: JSON.parse(JSON.stringify(self.params))};

		if (!return_url)
			console.debug("OLD STATE", old_state, "UPDATE", obj);

		let new_params    = self.all_params();

		if (obj.hasOwnProperty("view") && obj.view != self.view) {
			new_state.view = obj.view;
			new_state.args = {}; // new view - let's reset the args

			new_params    = self.all_params(new_state.view);

			// we are changing view, so let's initialize all params to default values and mark them as changed
			Object.entries(new_params).forEach(function ([key, val]) {
				if (!new_state.params.hasOwnProperty(key)) {  // param was not set by past view
					new_state.params[key] = val.default; // initialize to default
				}
			});
		}

		if (obj.hasOwnProperty("args")) {
			Object.entries(obj.args).forEach(function ([key, val]) {
				new_state.args[key] = cast(self.views[new_state.view].args[key], val)[0];
			});
		}

		if (obj.hasOwnProperty("params")) {
			Object.entries(obj.params).forEach(function ([key, val]) {
				new_state.params[key] = (val == null) ? new_params[key].default : val;
			});
		}

		let redirect   = !obj.hasOwnProperty("redirect") || obj.redirect;
	
		if (return_url) { // we just want the url
			return self.write_url(new_state);
		} else {
			// update current router
			this.view = new_state.view;
			this.args = new_state.args;
			this.params = new_state.params;

			console.log("NEW STATE", self.state());

			if (redirect) {
				console.log("REDIRECTING", self.write_url(new_state));
				window.history.pushState(self.state(), "",  self.write_url(new_state));
			} else {
				console.log("NO REDIRECT");
			}
		}

		return new_state;
	}
}
