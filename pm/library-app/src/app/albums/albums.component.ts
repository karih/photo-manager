import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-albums',
  templateUrl: './albums.component.html',
  styleUrls: ['./albums.component.css']
})
export class AlbumsComponent implements OnInit {

	constructor() { 
		console.log("AlbumsComponent.constructor()");
	}

  ngOnInit() {
		console.log("AlbumsComponent.ngOnInit()");
  }

}
