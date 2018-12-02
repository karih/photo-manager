'use strict';

class Photo extends React.Component {
	onKeyDown(e) { console.log("onKeyDown"); }
	onFocus() { console.log("onFocus"); }
	onChange() { console.log("onChange"); }
	onBlur() { console.log("onBlur"); }
	onMouseOver() { console.log("onMouseOver"); }
	onClick(e) { console.log('onClick'); }

	onError(e) {
		console.log("Caught error event", e, e.target, e.type);
		e.target.onerror = null;
		e.target.src = "/static/spinner.gif";
		e.target.width = 40;
		//={(e)=>{e.target.onerror = null; e.target.src="image_path_here"}}
	}
	
	render() {
		return (
			<div className="img-outer" onClick={this.props.onClick}>
				<div className="img-block">
					<div className="img-inner"><img src={this.props.file_url} onError={(...args) => this.onError(...args)} /></div>
					<div className="img-text"><p>{this.props.description}</p></div>
				</div>
			</div>
		)
	}
}

class PrevNextButton extends React.Component {
	//prev_class() { return "btn bnt-secondary" + (this.props.hasPrev ? "" : " disabled"); } 
	//next_class() { return "btn bnt-secondary" + (this.props.hasNext ? "" : " disabled"); } 
	prev_class() { return "btn btn-secondary" } 
	next_class() { return "btn btn-secondary" } 
	test() { return "btn btn-secondary"; }

	render() {
		return (
			<div className="btn-group">
				<button type="button" className={this.prev_class()} onClick={() => this.props.onPrev()}>&laquo;</button>
				<button type="button" className={this.next_class()} onClick={() => this.props.onNext()}>&raquo;</button>
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

class QueryField extends React.Component {
	render() {
		return (
			<input type="text" name="q" value={this.props.value} onChange={(event) => this.props.onChange(event.target.value)} />
		)
	}
}

class PhotoList extends React.Component {


	render() {
		let _photos = this.props.photos.map((photo) =>
			<Photo key={photo.id.toString()} onClick={() => this.props.onChangeState({view: "photo", args: {photo: photo.id}})} file_url={photo.files.m} description={photo.basename} />
		);
		return (
			<div className="photo-list">
				{_photos}
			</div>
		)
	}
}

class PhotoOverview extends React.Component {
	constructor(props) {
		console.log("PhotoOverview(", props,")");
		super(props);
		this.state = {photos: []};
	}

	componentDidMount() { this.query(); }

	query() {
		let self = this;
		fetch('/simple_search?q=' + this.props.params.q + '&offset=' + this.props.params.offset + '&limit=' + this.props.params.limit)
		.then(function(response) {
			return response.json();
		})
		.then(function(jres) {
			console.log("Found", jres.photos.length, "photos");
			self.setState({photos: jres.photos});
		});
	}

	componentDidUpdate(prevProps, prevState, snapshot) {
		console.log("componentDidUpdate", this.props, prevProps);
		if (
			this.props.params.sort   != prevProps.params.sort || 
			this.props.params.q      != prevProps.params.q || 
			this.props.params.offset != prevProps.params.offset) {
			console.log("Re-querying");
			this.query();
		}
	}

	render() {
        //<nav className="col-md-2 bg-light sidebar">
        //  <div className="sidebar-sticky">
        //    <h5>Filters</h5>

        //    <h5>Selection</h5>
        //    <ul className="nav flex-column">
        //      <li className="nav-item">Filters</li>
        //      <li className="nav-item">Selection</li>
        //    </ul>
        //  </div>
        //</nav>
		return ( 
			<div id="main">

        <main className="col-lg-10 ml-auto px-4" role="main">
					<SortButton current={this.props.params.sort} onClick={() => this.props.onChangeState({params: {sort: "~"}})} /> 
					<PrevNextButton hasPrev="true" hasNext="true" onPrev={() => this.props.onChangeState({params: {offset: this.props.params.offset-20}})} onNext={() => this.props.onChangeState({params: {offset: this.props.params.offset+20}})} />
					<QueryField value={this.props.params.q} onChange={(q) => this.props.onChangeState({params: {q: q}})} />
					<PhotoList onChangeState={this.props.onChangeState} photos={this.state.photos} params={this.props.params} /> 
				</main>
			</div> 
		)
	}
}

class PhotoSingle extends React.Component {
	render() {
		return (
			<div id="main">
				<main className="col-lg-12 px-4 photo-single" role="main">
					<button onClick={() => this.props.onChangeState({view: "photos"})} >Back to index</button>
					<Photo single_url="/static/_DSC5083_1600x1600.JPG" file_url="/static/_DSC5083_1600x1600.JPG" />
				</main>
			</div>
		);
	}

}
