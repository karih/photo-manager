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
			<div className="img-outer" onClick={this.props.onClick}>
				<div className="img-block">
					<div className="img-inner"><img src={this.props.file_url} /></div>
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

class PhotoList extends React.Component {
	render() {
		return (
			<div className="photo-list">
				<Photo onClick={() => this.props.onChangeState({view: "photo", args: {photo: 13}})} file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo onClick={() => this.props.onChangeState({view: "photo", args: {photo: 14}})} file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo onClick={() => this.props.onChangeState({view: "photo", args: {photo: 15}})} file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo onClick={() => this.props.onChangeState({view: "photo", args: {photo: 16}})} file_url="/static/_DSC5083_256x256.jpg" description="photo" />
				<Photo onClick={() => this.props.onChangeState({view: "photo", args: {photo: 17}})} file_url="/static/_DSC5083_256x256.jpg" description="photo" />
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
					<SortButton current={this.props.params.sort} onClick={() => this.props.onChangeState({params: {sort: "~"}})} /> 
					<PrevNextButton hasPrev="true" hasNext="true" onPrev={() => this.props.onChangeState({params: {offset: this.props.params.offset-20}})} onNext={() => this.props.onChangeState({params: {offset: this.props.params.offset+20}})} />
					<PhotoList onChangeState={this.props.onChangeState} /> 
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
