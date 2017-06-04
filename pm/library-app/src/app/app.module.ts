import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpModule, JsonpModule } from '@angular/http';
import { RouterModule, Routes } from '@angular/router';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { AppComponent } from './app.component';
import { BrowserComponent } from './photos/browser.component';
import { AlbumsComponent } from './albums/albums.component';
import { PaginatorComponent } from './photos/paginator.component';

// https://angular.io/docs/ts/latest/guide/router.html#!#basics
const appRoutes: Routes = [
	{ path: 'photos', component: BrowserComponent },	
	{ path: 'albums', component: AlbumsComponent },
	{ path: '', redirectTo: '/photos', pathMatch: 'full' }
];


@NgModule({
  declarations: [
    AppComponent,
    BrowserComponent,
		AlbumsComponent,
		PaginatorComponent
  ],
  imports: [
		NgbModule.forRoot(),
		RouterModule.forRoot(appRoutes),
    BrowserModule,
    FormsModule,
		HttpModule,
		JsonpModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { 
	//console.log("AppModule");
}
