import { Injectable } from '@angular/core';
import { Http, Response, RequestOptionsArgs } from '@angular/http';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/map';
import { Photo, Group, Entry } from '../photo';

export class SearchResult {
	hits: number;
	limit: number;
	next: number;
	offset: number;
	photos: Entry[];
	previous: number;
	sort_column: string;
	sort_order: string;

	constructor() { }


}

@Injectable() 
export class SearchService {

	constructor(private http: Http) {
		console.log("SearchService.constructor()");
	}

	search(params: any): Observable<SearchResult> {
		console.log("SearchService.search()");
		return this.http.get('/api/photos', {params: params})
										.map(this.parseResponse)
		                .catch(this.handleError);
	}

	private parseResponse(res: Response) {
		return res.json() || { };
	}

	private handleError (error: Response | any) {
    // In a real world app, you might use a remote logging infrastructure
    let errMsg: string;
    if (error instanceof Response) {
      const body = error.json() || '';
      const err = body.error || JSON.stringify(body);
      errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
    } else {
      errMsg = error.message ? error.message : error.toString();
    }
    console.error(errMsg);
    return Observable.throw(errMsg);
  }
}
