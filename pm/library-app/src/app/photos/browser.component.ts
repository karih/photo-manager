import { Component, OnInit } from '@angular/core';
import { SearchService, SearchResult } from './search';
import { Photo, Group, Entry } from '../photo';
import { ActivatedRoute, Router } from '@angular/router';


@Component({
  selector: 'app-photos-browser',
  templateUrl: './browser.component.html',
	styleUrls: ['./browser.component.css'],
	providers: [SearchService],
})
export class BrowserComponent implements OnInit {
	photos: Entry[];
	offset: number;
	limit: number;
	nentries: number;
	error = null;
	result: SearchResult;
	sort_columns = [{key: "date", title: "Date"}];
	limits = [10, 20, 50, 100];

	constructor(private searchService: SearchService, private route: ActivatedRoute, private router: Router) { 
		console.log("BrowserComponent.constructor()");
		console.log("BrowserComponent.constructor(", this.result, ")");
	}

  ngOnInit() {
		console.log("BrowserComponent.ngOnInit()");
		this.route.queryParams.subscribe(p => this.search(p));
		console.log("BrowserComponent.ngOnInit(", this.result, ")");
	}

	search(params: any) {
		console.log("BrowserComponent.search(", params, ")");
		this.searchService.search(params).subscribe(
			result => { this.onSearch(result) },
			error => this.error = error
		);
  }

	onSearch(result: SearchResult) {
		console.log("BrowserComponent.onSearch(", result, ")");
		this.result = result;
		console.log("/BrowserComponent.onSearch(", this.result, ")");
	}

	changePageEvent(event) {
		console.log("BrowserComponent.changePageEvent(", event, ")");
		this.changePage(event.offset, event.limit);
	}

	changePage(offset: number, limit: number) {
		console.log("BrowserComponent.changePage(", offset, ",", limit, ")");
		this.router.navigate(['/photos', ], {queryParams: {offset: offset, limit: limit}});
	}

	changeSortOrder(new_order: string) {
		console.log("BrowserComponent.changeSortOrder(", new_order, ")")
	}

	changeSortColumn(new_column: string) {
		console.log("BrowserComponent.changeSortColumn(", new_column, ")")
	}

	changeLimit(new_limit: number) {
		console.log("BrowserComponent.changeLimit(", new_limit, ")")
	}


	rass(event) {
		console.log("rass", this.result, this.photos);
	}
}
