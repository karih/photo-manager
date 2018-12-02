'use strict';

function cast(param, value) {
	var new_value = null;
	switch (param.type) {
		case "dual":
			if (param.values.indexOf(value) < 0) 
				new_value = param.default;
			else
				new_value = value;
			break;
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
		default:
			console.log("ERROR: Unknown parameter type");
	}

	return [new_value, new_value == null ? null : (new_value.toString() != value), new_value == param.default];
}

class Router {
	constructor(views, default_view) {
		this.views = views;
		this.default_view = default_view;
		this.view = null;
		this.params = {};
		this.args = {};
	}

	base_href() { return document.getElementsByTagName('base')[0].href; }

	all_params() {
		//console.log("all_params")
		let view = this.views[this.view];
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

	write_url() {
		//console.log("write_url()");
		let params = new URLSearchParams();
		let self = this;
		
		Object.entries(this.nondefault_params()).forEach(function ([key, val]) {
			//console.log("Adding argument ", key, " value ", val);
			params.append(key, val);
		});

		let view_url = this.views[this.view].url;
		Object.entries(this.views[this.view].args).forEach(function ([key, val]) {
			//console.log("view_url was", view_url)
			view_url = view_url.replace("<" + val.type + ":" + val.name + ">", self.args[key]);
			//console.log("view_url is", view_url)
		});


		var url = this.base_href() + view_url + (params.toString().length > 0 ? "?" : "") + params.toString();
		//console.log("Suggested URL: ", url, "params", params.toString());

		return url;
	}

	nondefault_params() {
		let out = {};
		let params = this.all_params();
		let self = this;
		Object.entries(params).forEach(function ([key, val]) {
			//console.log("nondefault_params()", "key", key, "val", val, "current value", self.params[key]);
			if (val.default != self.params[key])
				out[key] = self.params[key];
		});
		return out;
	}

	updateState(obj, redirect=true) {
		let self = this;
		var new_state = {};
		var old_state = {view: this.view, args: JSON.parse(JSON.stringify(this.args)), params: JSON.parse(JSON.stringify(this.params))};
		console.debug("OLD STATE", old_state);
		console.debug("UPDATE", obj);
		if (obj.hasOwnProperty("view")) {
			this.view = obj.view;
			new_state.view = obj.view;
			new_state.args = {};
			this.args = {}; // reset args 

			// initializing all params to default values and marking them as changed
			Object.entries(this.all_params()).forEach(function ([key, val]) {
				if (!self.params.hasOwnProperty(key)) { 
					if (!new_state.hasOwnProperty("params"))
						new_state.params = {}
					//console.log("Setting param", key, "value", val.default);
					self.params[key] = val.default;
					new_state.params[key] = self.params[key];
				}
			});
		}

		let view = this.views[this.view];
		let params = this.all_params();

		if (obj.hasOwnProperty("args")) {
			Object.entries(obj.args).forEach(function ([key, val]) {
				let old_value = self.args[key];
				let new_value = cast(view.args[key], val)[0];
				if (new_state.hasOwnProperty("view") || old_value != new_value) {
					if (!new_state.hasOwnProperty("args"))
						new_state.args = {}
					new_state.args[key] = new_value;
					self.args[key] = new_value;
					//console.log("Setting arg", key, "value", new_value);
				}
				//console.log("Updated argument", key, "to value", val);
			});
			new_state.args = this.args;
		}

		if (obj.hasOwnProperty("params")) {
			new_state.params = {}
			Object.entries(obj.params).forEach(function ([key, val]) {
				//console.log("param key", key, "val", val, "self.params", self.params, "all_params", params, "view", self.view);
				let old_value = self.params[key];
				let new_value = null;
				if (params[key].type == "dual" && val == "~") {
					//console.log(key, val, "flipping");
					new_value = params[key].values[1 - params[key].values.indexOf(self.params[key])];
				} else if (val == null) {
					//console.log(key, val, "defaulting");
					new_value = params[key].default;
				} else {
					//console.log(key, val, "setting");
					new_value = val;
				}
				if (new_state.hasOwnProperty("view") || old_value != new_value) {
					self.params[key] = new_value;
					new_state.params[key] = new_value;
					//console.log("Setting param", key, "value", new_value);
				}
			});
			new_state.params = this.params;
		}

		//console.log("Before redirect, view", this.view, "args", this.args, "params", this.params);
	
		if (redirect && Object.keys(new_state).length > 0) {
			console.log("PUSHING STATE", this.state(), this.write_url());
			window.history.pushState(this.state(), "",  this.write_url());
		} else {
			console.log("UPDATED STATE WITHOUT PUSHING TO HISTORY", this.state());
		}

		return new_state;
	}
}
