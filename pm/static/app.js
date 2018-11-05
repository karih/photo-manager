
'use strict';

class Header extends React.Component {
	render() {
    return (<header>
      <nav className="navbar navbar-expand-md navbar-dark fixed-top bg-dark">
        <a className="navbar-brand" href="/l">Photo Library</a>
        <div className="collapse navbar-collapse">
          <ul className="navbar-nav mr-auto">
            <li className="nav-item"><a className="nav-link" href="/l">Photos</a></li>
          </ul>
        </div>
      </nav>
    </header>)
	}
}


/* 
 *
 * NAEST: 
 * * LESA INN URL og greina view og state variables
 * * UPPFAERA url on state change
 * * PREVENTA redirect ef base urlid er ekki ad breytast 
 * * GERA DATE filter
 * * TENGJAST bakenda
 */


class App extends React.Component {
	constructor(props) {
		super(props);

		this.state_vars = {
			sort:   {type: "dual", values: ["asc", "desc"]},
			offset: {type: "int", default: 0},
			limit:  {type: "int", default: 20},
		}
		
		var global_state = new URLSearchParams(window.location.search);
			
		this.state = {
			sort: global_state.has("sort") && ["asc", "desc"].includes(global_state.get("sort")) ? global_state.get("sort") : "asc",
		}

	}


	updateState(variable, value) {
		console.log("updateState(", variable, ",", value, ")");
		var obj = {}
		obj[variable] = value
		this.setState(obj);
		var global_state = new URLSearchParams(window.location.search);
		global_state.set(variable, value);
		window.location.search = global_state.toString();

	}

	onChangeState(variable, value) {
		console.log("onChangeState(", variable, ",", value, ")");

		if (!this.state_vars.hasOwnProperty(variable)) {
			console.log("Tried to set invalid state variable", variable, "to value", value)
			return
		}
		
		if (typeof(value) == "undefined") {
			// now value was passed
			if (this.state_vars[variable].hasOwnProperty("bool") && this.state_vars[variable].bool === true) {
				this.updateState(variable, this.state_vars[variable].values[1 - this.state_vars[variable].values.indexOf(this.state[variable])]);
			} else {
				console.log("reached else A");
			}
		} else {
			console.log("reached else B");
		}
	}
	
	/*
	changeSort() {
		var global_state = new URLSearchParams(window.location.search);
		if (this.state.sort == "asc") {
			this.setState({sort: "desc"});
			global_state.set("sort", "desc");
		} else {
			this.setState({sort: "asc"});
			global_state.set("sort", "asc");
		}
		window.location.search = global_state.toString();
	}
	*/

	onChangeView(new_view) { }

	test() {
		this.setState({sort: "desc"});
	}

	render() {
		return (
			<div>
				<Header />
				<div className="container-fluid">
					<div className="row">
						<PhotoOverview onChangeState={(...args) => this.onChangeState(...args)} state={this.state} />
					</div>
				</div>
				<button type="button" onClick={() => this.test()}>test test</button>
				<p> state is {JSON.stringify(this.state)}</p>
			</div>
		)
	}
}
