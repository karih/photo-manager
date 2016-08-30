var app = angular.module('pm', ['ui.router']).config(function($rootScopeProvider){
	$rootScopeProvider.digestTtl(20); // for the tree recursion
});

app.config(['$stateProvider', '$locationProvider', '$urlRouterProvider', '$urlMatcherFactoryProvider',
	function($stateProvider, $locationProvider, $urlRouterProvider, $urlMatcherFactoryProvider) {
    $urlMatcherFactoryProvider.type("nonURIEncoded", {
        encode: function(val) { return val != null ? val.toString() : val; },
        decode: function(val) { return val != null ? val.toString() : val; },
        is: function(val) { return true; }
    });

		$stateProvider
			.state('file-manager', {
				abstract: true,
				url: '/files',
				template: '<ui-view />'
			})
			.state('file-manager.single', {
				url: '/{id:int}',
				templateUrl: '/static/partials/file-manager-single.html',
				controller: 'FileManagerSingleCtrl'
			})
			.state('file-manager.overview', {
				url: '/overview{path:nonURIEncoded}?{offset:int}&{limit:int}',
				templateUrl: '/static/partials/file-manager-overview.html',
				controller: 'FileManagerOverviewCtrl',
				params: { 
					path: { dynamic: true, value: "/" }, 
					offset: {dynamic: true, value: 0}, 
					limit: {dynamic: true, value: 20}
				},
			})
			.state('photos', {
				url: '/photos',
				templateUrl: '/static/partials/photos/photos.html',
				controller: 'PhotosOverviewCtrl',
				params: {
					offset: {dynamic: true, value: 0}, 
					limit: {dynamic: true, value: 20}
				}
			})
			.state('photos.single', {
				url: '/{id:int}',
				templateUrl: '/static/partials/photos/photos.html',
				controller: 'PhotoCtrl'
			});


		$urlRouterProvider.otherwise('/files/overview');

		$locationProvider.html5Mode(true);
	}]);

