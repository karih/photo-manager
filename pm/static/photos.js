'use strict';

class Photo extends React.Component {
	onKeyDown(e) { console.log("onKeyDown"); }
	onFocus() { console.log("onFocus"); }
	onChange() { console.log("onChange"); }
	onBlur() { console.log("onBlur"); }
	onMouseOver() { console.log("onMouseOver"); }
	onClick(e) { console.log('onClick'); }

	onError(e) {
		//console.log("Caught error event", e, e.target, e.type);
		//e.target.onerror = null;
		let img = e.target;
		let oldsrc = img.src;
		//let oldwidth = img.width;

		img.src = "/static/spinner.gif";
		//img.width = 40;
		//={(e)=>{e.target.onerror = null; e.target.src="image_path_here"}}
		setTimeout(() => {
			img.src = oldsrc;
			//img.width = oldwidth;
    }, 2000);
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
	render() {
		return (
			<div className="form-inline">
				<p className="my-1 mr-2 form-text">{this.props.offset+1}&ndash;{this.props.offset+this.props.limit} of {this.props.count}</p>
				<div className="btn-group mr-2">
					<button 
						disabled={this.props.offset <= 0} 
						type="button" 
						className="btn btn-secondary" 
						onClick={() => this.props.onPrev()}>&laquo; Previous Page</button>
					<button 
						disabled={this.props.offset + this.props.limit > this.props.count} 
						type="button" 
						className="btn btn-secondary" 
						onClick={() => this.props.onNext()}>Next Page &raquo;</button>
				</div>

				<label htmlFor="limit">Results/page:</label>
				<select value={this.props.limit} name="limit" className="custom-select" onChange={(event) => this.props.onChangeLimit(event.target.value)}>
					<option value="20">20</option>
					<option value="40">40</option>
					<option value="80">80</option>
					<option value="100">100</option>
				</select>
			</div>
		)
	}
}

class SortControl extends React.Component {
	order_action_text() { return this.props.current == "asc" ? "Descending" :"Ascending"; }
	order_text() { return this.props.current == "asc" ? "Ascending" : "Descending"; }

	render() {
		return (
			<div className="form-inline mr-2">
			  <label className="my-1 mr-2" htmlFor="sort-column">Sort Column</label>
				<select value={this.props.currentColumn} name="sort-column" className="custom-select" onChange={(event) => this.props.onChangeColumn(event.target.value)}>
					<option value="id">#id</option>
					<option value="date">Date</option>
				</select>
				<select value={this.props.currentOrder} className="custom-select" onChange={(event) => this.props.onChangeOrder(event.target.value)}>
					<option value="asc">Ascending</option>
					<option value="desc">Descending</option>
				</select>
			</div>
		)
			//<div className="btn-group mr-2">
			//	<button type="button" className="btn btn-secondary" onClick={() => this.props.onClick()}>Sort {this.order_action_text()}</button>
			//</div>
	}
}

class QueryField extends React.Component {
	render() {
		return (
			<div className="form-inline">
				<label htmlFor="q">Search Query: </label>
				<input 
					type="text" 
					className="form-control" 
					id="q"
					name="q" 
					value={this.props.value} 
					onChange={(event) => this.props.onChange(event.target.value)} 
				/>
			</div>
		)
	}
}

class PhotoList extends React.Component {
	render() {
			//<a key={photo.id.toString()} href={this.props.onChangeState({view: "photo", args: {photo: photo.id}, url: true})} onClick={() => this.props.onChangeState({view: "photo", args: {photo: photo.id}})}>
			//	<Photo  file_url={photo.sizes.m} description={photo.basenames.toString()} />
			//</a>
		let _photos = this.props.photos.map((photo) =>
			<Link key={photo.id.toString()} newState={{view: "photo", args: {photo: photo.id}}}>
				<Photo  file_url={photo.sizes.m} description={photo.basenames.toString()} />
			</Link>
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
		fetch('/simple_search?q=' + this.props.params.q + '&offset=' + this.props.params.offset + '&limit=' + this.props.params.limit + '&sort_column=' + this.props.params.sort_column + '&sort_order=' + this.props.params.sort_order)
		.then(function(response) {
			return response.json();
		})
		.then(function(jres) {
			self.setState({photos: jres.photos, count: jres.count});
			console.log("Updating state, results", jres.photos.length, "total count", jres.count);
		});
	}

	componentDidUpdate(prevProps, prevState, snapshot) {
		//console.log("componentDidUpdate", this.props, prevProps);
		if (
			this.props.params.sort_column != prevProps.params.sort_column || 
			this.props.params.sort_order  != prevProps.params.sort_order || 
			this.props.params.q           != prevProps.params.q || 
			this.props.params.limit       != prevProps.params.limit || 
			this.props.params.offset      != prevProps.params.offset) {
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
		console.log("INITIAL VALUES", this.props.params.sort_column, this.props.params.sort_order);
		return ( 
			<main className="col-lg-12 px-4 photo-list" role="main">
				<div className="btn-toolbar mt-3 mb-3" role="toolbar" aria-label="Toolbar with button groups">
					<SortControl 
						currentColumn={this.props.params.sort_column} 
						currentOrder={this.props.params.sort_order} 
						onChangeOrder={(ord) => this.props.onChangeState({params: {sort_order: ord}})} 
						onChangeColumn={(col) => this.props.onChangeState({params: {sort_column: col}})} 
						/> 
					<PrevNextButton 
						offset={this.props.params.offset}
						limit={this.props.params.limit}
						count={this.state.count}
						onPrev={() => this.props.onChangeState({params: {offset: Math.max(0, this.props.params.offset-this.props.params.limit)}})} 
						onNext={() => this.props.onChangeState({params: {offset: this.props.params.offset+this.props.params.limit}})} 
						onChangeLimit={(limit) => this.props.onChangeState({params: {limit: limit}})} 
					/>
					<QueryField value={this.props.params.q} onChange={(q) => this.props.onChangeState({params: {q: q, offset: 0}})} />
				</div>
				<PhotoList onChangeState={this.props.onChangeState} photos={this.state.photos} params={this.props.params} /> 
			</main>
		)
	}
}

class PhotoSingle extends React.Component {
	//http://localhost:8000/simple_search?q=id:99
	constructor(props) {
		console.log("PhotoSingle(", props,")");
		super(props);
		this.state = {all_labels: [], labels: []};
	}

	componentDidMount() { this.get_photo(); this.get_labels(); }

	get_photo() {
		let self = this;
		fetch('/api/photo/' + this.props.args.photo)
		.then(function(response) {
			return response.json();
		})
		.then(function(jres) {
			console.log("Found photo", jres);
			let obj = jres.photo;
			obj.label = obj.labels.map((x) => x.id); 

			console.log("LABEL", obj.label)
			self.setState(obj);
		});
	}

	get_labels() {
		let self = this;
		fetch('/api/labels')
		.then(function(response) {
			return response.json();
		})
		.then(function(jres) {
			console.log("Found", jres.labels.length, "labels");
			self.setState({all_labels: jres.labels});
		});
	}

	//componentDidUpdate(prevProps, prevState, snapshot) {
	//	//console.log("componentDidUpdate", this.props, prevProps);
	//	if (this.props.args.photo != prevProps.args.photo) {
	//		console.log("Re-querying");
	//		this.query();
	//	}
	//}
	
	updateLabels(event) {
		let new_labels = [];
		for (let i=0; i < event.target.options.length; i++) {
			if (event.target.options[i].selected)
				new_labels.push(Number.parseInt(event.target.options[i].value));
		}
		console.log("Update labels", new_labels);
		this.setState({label: new_labels});

		let self = this;
		fetch('/api/photo/' + this.state.id, {
			method: "PUT",
			headers: {"Content-Type": "application/json; charset=utf-8"},
			body: JSON.stringify({labels: new_labels})
		})
		.then(function(response) {
			console.log("LABEL UPDATE RESPONSE", response);
			//return response.json();
		})
	}

	labels() {
		return this.state.all_labels.map((label) =>
			<option key={label.id} value={label.id}>{label.label}</option>
		);
	}

	render() {
		if (this.state.hasOwnProperty("sizes")) {
			return (
				<main className="col-lg-12 px-4 mx-auto photo-single" role="main">
					<div className="btn-toolbar mt-2 mb-2">
						<Link className="btn btn-secondary mr-2" newState={{view: "photos"}}>Back to index</Link>
						<a className="btn btn-secondary mr-2" href={this.state.sizes.o}>Download</a>
					</div>
					<div className="form-inline">
						<label htmlFor="labels">Labels:</label>
						<select value={this.state.label} id="labels" name="labels" multiple className="custom-select" onChange={(event) => this.updateLabels(event)}>
							{this.labels()}
						</select>
					</div>
					<Photo file_url={this.state.sizes.z} />
				</main>
			);
		} else {
			return (
				<main className="col-lg-12 px-4 mx-auto photo-single" role="main">
					<button className="btn btn-secondary" onClick={() => this.props.onChangeState({view: "photos"})} >Back to index</button>
					Loading...
				</main>
			);
		}
	}

}
