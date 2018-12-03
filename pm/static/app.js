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
		this.views = {
			photos: {
				view: (args, params, onChangeState) => <PhotoOverview onChangeState={(...args) => onChangeState(...args)} args={args} params={params} />, 
				url: 'index',
				params: {
					q:          {type: "string", default: "*"},
					sort_order: {type: "dual",   values: ["asc", "desc"], default: "asc"},
					sort_column:{type: "string", values: ["id", "date"], default: "date"},
					offset:     {type: "int", default: 0},
					limit:      {type: "int", default: 20},
				},
			},
			photo: {
				view: (args, params, onChangeState) => <PhotoSingle onChangeState={(...args) => onChangeState(...args)} args={args} params={params} />, 
				inherit: 'photos', 
				url: 'index/single/<int:photo>',
				params: {}
			}
		};

		this.router = new Router(this.views, 'photos');
		this.router.read();
		this.state_vars = this.router.views[this.router.view].params;
		this.state = {args: this.router.args, params: this.router.params};

		window.addEventListener('popstate', (event) => this.setState(this.router.updateState(event.state, false)));
	}

	onChangeState(update) {
		if (update.hasOwnProperty("url") && update.url)
			return this.router.updateState(update);
		else
			this.setState(this.router.updateState(update));
	}
	
	render() {
		var _view = this.router.views[this.router.view].view;
		console.log("_view", _view, this.router.view, this.router.views);
		return (
			<div>
				<Header />
				<div className="container-fluid">
					<div className="row">
						{_view(this.state.args, this.state.params, (...args) => this.onChangeState(...args))}
					</div>
				</div>
				<p> state is {JSON.stringify(this.state)}</p>
			</div>
		)
		//<button type="button" onClick={() => this.test()}>test test</button>
	}
}
