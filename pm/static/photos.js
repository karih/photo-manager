'use strict';

class Photo extends React.Component {
	onKeyDown(e) { console.log("onKeyDown"); }
	onFocus() { console.log("onFocus"); }
	onChange() { console.log("onChange"); }
	onBlur() { console.log("onBlur"); }
	onMouseOver() { console.log("onMouseOver"); }

	onClick(e) { console.log('onClick'); }

	render() {
		return (
			<div className="img-outer" onClick={this.onClick}>
				<div className="img-block">
					<div className="img-inner"><img src={this.props.file_url} /></div>
					<div className="img-text"><p>{this.props.description}</p></div>
				</div>
			</div>
		)
	}
}

class SortButton extends React.Component {
	order_action_text() { return this.props.current == "asc" ? "Descending" :"Ascending"; }
	order_text() { return this.props.current == "asc" ? "Ascending" : "Descending"; }

	render() {
		return (
			<div className="btn-group">
				<button type="button" className="btn btn-secondary" onClick={() => this.props.onClick()}>Sort {this.order_action_text()}</button>
			</div>
		)
	}
}

class PhotoList extends React.Component {
	render() {
		return (
			<div className="photo-list">
				<Photo single_url="/static/_DSC5083_256x256.jpg" file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo single_url="/static/_DSC5083_256x256.jpg" file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo single_url="/static/_DSC5083_256x256.jpg" file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo single_url="/static/_DSC5083_256x256.jpg" file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo single_url="/static/_DSC5083_256x256.jpg" file_url="/static/_DSC5083_256x256.jpg" description="photo" />
			</div>
		)
	}
}

class PhotoOverview extends React.Component {
	constructor(props) {
		console.log("PhotoOverview(", props,")");
		super(props);
	}

	render() {
		return ( 
			<div id="main">
        <nav className="col-md-2 bg-light sidebar">
          <div className="sidebar-sticky">
            <h5>Filters</h5>

            <h5>Selection</h5>
            <ul className="nav flex-column">
              <li className="nav-item">Filters</li>
              <li className="nav-item">Selection</li>
            </ul>
          </div>
        </nav>

        <main className="col-lg-10 ml-auto px-4" role="main">
					<SortButton current={this.props.state.sort} onClick={() => this.props.onChangeState("sort")} /> 
					<PhotoList /> 
				</main>
			</div> 
		)
	}
}
