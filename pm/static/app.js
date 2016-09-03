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
			.state('file-manager.tree', {
				url: '/tree{path:nonURIEncoded}?{offset:int}&{limit:int}',
				templateUrl: '/static/partials/file-manager-overview.html',
				controller: 'FileManagerOverviewCtrl',
				params: { 
					path: { dynamic: true, value: "/" }, 
					offset: {dynamic: true, value: 0}, 
					limit: {dynamic: true, value: 20}
				},
			})
			.state('photos', {
				abstract: true,
				url: "/photos",
				template: "<ui-view />"
			})
			.state('photos.list', {
				url: '?{offset:int}&{limit:int}&date&aperture&exposure&focal_length&focal_length_35&iso&make&model&lens',
				templateUrl: '/static/partials/photos/photos.html',
				controller: 'PhotosOverviewCtrl',
				params: {
					offset: {dynamic: true, value: 0}, 
					limit: {dynamic: true, value: 20},
					date: {dynamic: true, value: null},
					aperture: {dynamic: true, value: null},
					exposure: {dynamic: true, value: null},
					focal_length: {dynamic: true, value: null},
					focal_length_35: {dynamic: true, value: null},
					iso: {dynamic: true, value: null},
					make: {dynamic: true, value: null},
					model: {dynamic: true, value: null},
					lens: {dynamic: true, value: null}
				}
			})
			.state('photos.details', {
				url: '/{id:int}',
				templateUrl: '/static/partials/photos/single.html',
				controller: 'PhotoCtrl',
				params: {
					id: {dynamic: true, value: 0}
				}
			});

		$urlRouterProvider.otherwise('/files/tree');

		$locationProvider.html5Mode(true);
	}]);

