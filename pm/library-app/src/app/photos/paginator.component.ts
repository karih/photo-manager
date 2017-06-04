import { Component, OnInit, OnChanges, SimpleChanges, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-photos-paginator',
  templateUrl: './paginator.component.html',
	styleUrls: ['./paginator.component.css'],
	providers: [],
})
export class PaginatorComponent implements OnInit, OnChanges {
	@Input() hits: number;
	@Input() offset: number;
	@Input() limit: number;
	@Input() nentries: number;

	@Output() changePageRequest: EventEmitter<any> = new EventEmitter();

	pages: any[];
	current_page: number;
	previous_offset: number;
	next_offset: number;

	constructor() { 
		console.log("PaginatorComponent.constructor()");
	}

  ngOnInit() {
		console.log("PaginatorComponent.ngOnInit()");
  }

	ngOnChanges(changes: SimpleChanges) {
		console.log("PaginatorComponent.ngOnChange()");
		this.updatePages();
	}

	private updatePages() {
		let near = 3;
		let pgs = new Set();
		this.current_page = Math.floor(this.offset / this.limit) + 1;
		let last_page     = Math.floor(this.hits / this.limit) + 1;
		let max_records   = 1000;

		this.previous_offset = this.offset == 0 ? null : Math.max(0, this.offset - this.limit);
		this.next_offset     = ((this.hits <= this.offset + this.limit) || (this.offset + 2*this.limit > max_records)) ? null : this.offset + this.limit;

		for(let i=0; i < near; i++) {
			pgs.add(Math.min(1+i, last_page));
			pgs.add(Math.max(1, last_page-i));
			pgs.add(Math.min(this.current_page + i, last_page));
			pgs.add(Math.max(this.current_page - i, 1));
		}

		this.pages = [];
		for (let i=1; i <= last_page; i++) {
			if (pgs.has(i)) {
				this.pages.push({
					seq: true,
					page: i,
					current: this.current_page == i,
					offset: this.limit*(i-1),
					first: i == 1,
					last: i == last_page,
					disabled: this.limit*i > max_records
				});
			} else if (this.pages[this.pages.length-1].seq == true) {
				this.pages.push({seq: false});
			}
		}
	}

	changePage(new_offset: number) {
		this.changePageRequest.emit({offset: new_offset, limit: this.limit});
	}
}
