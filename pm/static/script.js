'use strict';

console.log("rass");

window.addEventListener('beforeunload', function(e) {
	console.log('beforeunload(', e, ')');
	//e.preventDefault();
	//e.returnValue = '';
	
});

window.addEventListener('popstate', function(e) {
	console.log('popstate(', e, ')');
});
window.addEventListener('pushstate', function(e) {
	console.log('pushstate(', e, ')');
});
window.addEventListener('hashchange', function(e) {
	console.log('hashchange(', e, ')');
});


function router() {
	URLSearchParams(location.search);
	window.onbeforeunload
	window.onpopstate
	window.onhashchange
	window.location.hash
	window.history.back
	window.history.forward
	window.history.pushState
	window.location.pathname
	window.location.search
}

ReactDOM.render(React.createElement(App, null), document.getElementById('app'));
