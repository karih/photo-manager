import { Injectable } from '@angular/core';

export abstract class Entry {
	id: number;
	thumb_url: string;

	constructor() {
		console.log("Entry.constructor()")
	}
}

export class Derivative extends Entry {
	constructor() {
		super();
		console.log("Derivative.constructor()")
	}
}

export class File extends Entry {
	constructor() {
		super();
		console.log("File.constructor()")
	}
}

export class Photo extends Entry {
	constructor() {
		super();
		console.log("Photo.constructor()")
	}
}

export class Group extends Entry {
	constructor() {
		super();
		console.log("Group.constructor()")
	}
}

