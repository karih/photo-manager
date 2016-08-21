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
			.state('file-manager-single', {
				url: '/file-manager-single/:id',
				templateUrl: '/static/partials/file-manager-single.html',
				controller: 'FileManagerSingleCtrl'
			})
			.state('file-manager-overview', {
				url: '/file-manager-overview{path:nonURIEncoded}?{offset:int}&{limit:int}',
				templateUrl: '/static/partials/file-manager-overview.html',
				controller: 'FileManagerOverviewCtrl',
				params: { 
					path: { dynamic: true, value: "/" }, 
					offset: {dynamic: true, value: 0}, 
					limit: {dynamic: true, value: 20}
				},
			});

		$urlRouterProvider.otherwise('/file-manager-overview');

		$locationProvider.html5Mode(true);
	}]);

