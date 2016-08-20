var app = angular.module('pm', ['ui.router']).config(function($rootScopeProvider){
	$rootScopeProvider.digestTtl(20);
});

app.config(['$stateProvider', '$locationProvider', '$urlRouterProvider', '$urlMatcherFactoryProvider',
	function($stateProvider, $locationProvider, $urlRouterProvider, $urlMatcherFactoryProvider) {
		console.log("pm.config()");

    $urlMatcherFactoryProvider.type("nonURIEncoded", {
        encode: function(val) { return val != null ? val.toString() : val; },
        decode: function(val) { return val != null ? val.toString() : val; },
        is: function(val) { return true; }
    });

		$stateProvider
			.state('file-single', {
				url: '/file-single/:id',
				templateUrl: '/static/partials/file-single.html',
				controller: 'SingleCtrl'
			})
			.state('file-overview', {
				url: '/file-overview{path:nonURIEncoded}?{offset:int}&{limit:int}',
				templateUrl: '/static/partials/file-overview.html',
				controller: 'OverviewCtrl',
				params: { path: { dynamic: true, value: "/" }, offset: {dynamic: true, value: 0}, limit: {dynamic: true, value: 20}},
			});

		$urlRouterProvider.otherwise('/file-overview');

		$locationProvider.html5Mode(true);
		console.log("/pm.config()");
	}]);

app.controller('OverviewCtrl', ['$scope', '$http', '$stateParams', '$state', '$document', function($scope, $http, $stateParams, $state, $document) {
	console.log("OverviewCtrl(" + $stateParams["path"] + ", " + $stateParams["offset"] + ", " + $stateParams["limit"] + ")");	

	$scope.limit = $stateParams["limit"];
	$scope.offset = $stateParams["offset"];
	$scope.path = $stateParams["path"];

	$document.bind('keydown', function(event, args) {
		if (event.keyCode == 39) {
			$state.go('file-overview', {path: $scope.path, offset: $scope.images.length < $scope.limit ? $scope.offset : $scope.offset + $scope.limit, limit: $scope.limit});
		} else if (event.keyCode == 37) {
			$state.go('file-overview', {path: $scope.path, offset: Math.max(0, $scope.offset-$scope.limit), limit: $scope.limit});

		}	
	});

	this.fetch = function(path, offset, limit) {
		console.log("FETCHING " + path + " o: " + offset + " l:" + limit);
		$http.get('/api/files', { params: {filter: path, offset: offset, limit: limit} }).success(function(data) {
			$scope.images = data.images;
		});
	}

	$scope.toggle_image = function(event, image) {
		if (!event.ctrlKey) {
			console.log("image clicked");
			if (image.hasOwnProperty("expanded")) {
				delete image.expanded;
			} else {
				$http.get('/api/file/' + image.id).success(function(data) {
					angular.forEach(data.image, function(value, key) {
						image.expanded = true;
						image[key] = value;
					});
				});
			}
			event.preventDefault();
		} else {
			return true;
		}
	}

	this.uiOnParamsChanged = function (changedParams, $transition$) {
		console.log("CHANGED");
		console.log(changedParams);
		$scope.path   = changedParams.hasOwnProperty("path")   ? changedParams.path : $scope.path;
		$scope.offset = changedParams.hasOwnProperty("offset") ? changedParams.offset : $scope.offset;
		$scope.limit  = changedParams.hasOwnProperty("limit")  ? changedParams.limit : $scope.limit;
		this.fetch($scope.path, $scope.offset, $scope.limit);
	};


	this.fetch($scope.path, $scope.offset, $scope.limit);

}]);

app.controller('SingleCtrl', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {
	console.log("SingleCtrl()");	

	$http.get('/api/file/' + $stateParams["id"]).success(function(data) {
		$scope.image = data.image;
	});
}]);

app.controller('FilesystemTreeCtrl', ['$scope', '$http', '$stateParams', 'tree_toggle_collapse', function($scope, $http, $stateParams, tree_toggle_collapse) {
	console.log("FilesystemTreeCtrl(" + $scope.path + ")");	

	$scope.root = {name: '/', path:'/', children: [], collapsed: true, current: $scope.path.length < 2};
	$scope.toggle_collapse = tree_toggle_collapse.collapse;

	$scope.$watch("path", function() {
		var recurse = function(nodes) {
			angular.forEach(nodes, function(v) {
				v.current = (v.path === $scope.path) ? true : false;
				if (v.children.length > 0)
					recurse(v.children);
			});
		};

		$scope.root.current = $scope.path.length < 2 ? true : false;
		recurse($scope.root.children);
	});

	$http.get('/api/filesystem').success(function(data) {
		var recurse = function(tree, path, node_collapsed) {

			var children = [];

			angular.forEach(tree, function(v, k) {
				var subpath = path + "/" + k;
				var hidden = node_collapsed;
				var collapsed = true;
				var current = false;

				if ($scope.path.substr(0, subpath.length) == subpath) {
					hidden = false;
					$scope.root.collapsed = false;
					if ($scope.path.length > subpath.length) {
						console.log(subpath)
						collapsed = false;
					}
				}

				if ($scope.path == subpath) {
					current = true;
				}

				var children_inner = recurse(v, subpath, collapsed);
				if (children_inner.length == 0) {
					collapsed = null;
				}

				children.push({name: k, path: subpath, hidden: hidden, collapsed: collapsed, current: current, children: children_inner}); 
			});

			return children;
		}

		$scope.root.children = recurse(data.filesystem, "", true);
	})

}]);

app.factory('tree_toggle_collapse', function() {
	var collapse = function(event, node, collapsing) {
		if (node.children.length > 0) {
			if (typeof collapsing === "undefined") {
				console.log(node.path);
				collapsing = (node.collapsed === false);
			}

			node.collapsed = collapsing;
			angular.forEach(node.children, function(v, k) {
				v.hidden = collapsing;
				if (event.ctrlKey || collapsing) { collapse(event, v, collapsing); } 
			});
		}
	};
	return { collapse: collapse };
});


app.directive('fsnodes', function() {
	return {
		restrict: "E",
		replace: true,
		scope: {
			nodes: '=nodes'
		},
		template: "<ul><fsnode ng-repeat='value in nodes' node='value'></fsnode></ul>"
	}
});

app.directive('fsnode', ['tree_toggle_collapse', function(tree_toggle_collapse) {
	return {
		restrict: "E",
		replace: true,
		scope: {
			node: '='
		},
		templateUrl: '/static/partials/filesystem-node.html',
		link: function(scope, element, attrs) {
			scope.toggle_collapse = tree_toggle_collapse.collapse;
		}
	}
}]);

app.filter('bytes', function() {
	return function(bytes, precision) {
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
		if (bytes === 0) return '0';
		if (typeof precision === 'undefined') precision = 1;
		var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
	}
});

app.filter('truncate_filename', function() {
	return function(str, len) {
		if (typeof(str) === "undefined") {
			return str;
		} else if (str.length <= len) {
			return str;
		} else {
			var bf = Math.floor(len/2)-1;
			var ef = Math.ceil(len/2)-2;

			console.log(len, bf, ef);
			
			return str.substring(0,bf) + "..." + str.substring(str.length-ef);
		}
	}
});
