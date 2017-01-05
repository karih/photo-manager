
app.controller('PhotosOverviewCtrl', ['$scope', '$http', '$stateParams', '$state', '$document', '$filter', function($scope, $http, $stateParams, $state, $document, $filter) {
	console.log("PhotosOverviewCtrl(", $stateParams, ")")

	$scope.offset = $stateParams["offset"];
	$scope.limit = $stateParams["limit"];
	$scope.state = JSON.parse(JSON.stringify($stateParams));

	$scope.sort_columns = {date: "Date", size: "Size"};
	$scope.default_sort_column = "date";
	$scope.limits = [10, 20, 50, 100];

	$scope.photos = null;
	$scope.photo = null;
	$scope.prev = null;
	$scope.next = null;
	$scope.hits = null;
	
	var scrollToTop = function() {
		$('html, body').animate({ scrollTop: -10000 }, 200);
		//document.body.scrollTop = document.documentElement.scrollTop = 0;
	}

	$scope.$on('stateChangeSuccess', function(event) {
		$scope.fetch(); // TODO check if custom event can be replaced by $transitions 
	});

	$scope.fetch = function() {
		if ($stateParams["id"] === null) {
			$scope.photo = null;
			$scope.prev = null;
			$scope.next = null;

			$http.get('/api/photos', {params: $stateParams}).success(function(data) {
				$scope.photos = data.photos;
				$scope.meta = {
					offset: data.offset, 
					limit: data.limit, 
					hits: data.hits, 
					sort_column: data.sort_column, 
					sort_order: data.sort_order
				};
			});
		} else {
			scrollToTop();

			$scope.photo = {};

			$http.get('/api/photo/' + $stateParams["id"]).success(function(data) {
				angular.forEach(data.photo, function(val, key) {
					$scope.photo[key] = data.photo[key];
				});
			});
			
			$http.get('/api/photos', {params: $stateParams}).success(function(data) {
				var previdx = null;
				var nextidx = null;
				var curidx  = null;

				angular.forEach(data.photos, function(val, key) {
					if (val.id == $stateParams["id"]) {
						curidx = key;
					}
				});
				$scope.prev = JSON.parse(JSON.stringify($stateParams));
				$scope.next = JSON.parse(JSON.stringify($stateParams));

				previdx = curidx - 1;
				nextidx = curidx + 1;

				$scope.photo.position = curidx + data.offset;
				$scope.photo.hits = data.hits;

				if (previdx < 0 && data.previous !== null) {
					$scope.prev["id"] = data.previous;
					$scope.prev["offset"] = Math.max(0, data.offset-data.limit);
				} else if (previdx >= 0) {
					$scope.prev["id"] = data.photos[previdx].id;
				} else {
					$scope.prev = null;
				}

				if (nextidx >= data.photos.length && data.next !== null) {
					$scope.next["id"] = data.next;
					$scope.next["offset"] = data.offset + data.limit;
				} else if (nextidx < data.photos.length) {
					$scope.next["id"] = data.photos[nextidx].id;
				} else {
					$scope.next = null;
				}	
			});
		}
	}

	$document.bind('keydown', function(event, args) {
		//var new_state = JSON.parse(JSON.stringify($stateParams));
		if ($scope.photo === null && event.keyCode == 39 && ($scope.meta.offset + $scope.meta.limit <= $scope.meta.hits)) {
			$scope.switchPage($scope.meta.offset + $scope.meta.limit, $scope.meta.limit);
			$scope.$apply();
		} else if ($scope.photo !== null && event.keyCode == 39 && $scope.next !== null) {
			$state.go('photos', $scope.next);
		} else if ($scope.photo === null && event.keyCode == 37) {
			$scope.switchPage(Math.max(0, $scope.meta.offset - $scope.meta.limit), $scope.meta.limit);
			$scope.$apply();
		} else if ($scope.photo !== null && event.keyCode == 37 && $scope.prev !== null) {
			$state.go('photos', $scope.prev);
		}	
	});

	$scope.$on('$destroy', function() {
		$document.unbind('keydown');
	});

	this.uiOnParamsChanged = function (changedParams, $transition$) {
		console.log("this.uiOnParamsChanged(", changedParams, ")");
		/* state called again with changed parameters */



		angular.forEach(changedParams, function(value, key) {
			$stateParams[key] = value;
			if ($scope.state[key] !== value)
				$scope.state[key] = value;
		})

		$scope.$broadcast('stateChangeSuccess', changedParams, $stateParams);
	};

	$scope.$watch('state', function(new_val, old_val) {
		//console.log('initiating state change due to changes in $scope.state', new_val, old_val);
		var new_expanded = null;
		var viewstates = ["dnv", "lv", "mv"];
		var expanded = 0;
		angular.forEach(viewstates, function(val) {
			if (new_val[val] == 2) {
			 if (old_val[val] < 2)
					new_expanded = val;
				expanded += 1;
			}
		});
		if (expanded > 1) {
			angular.forEach(viewstates, function(val) {
				if (new_val[val] == 2 && new_expanded !== val) {
					new_val[val] = 1;
				}
			});
		}

		var changable = ["date", "model", "dirname", "lens", "sort"];

		angular.forEach(changable, function(val) {
			if (new_val[val] !== old_val[val]) {
				new_val["offset"] = 0;
			}
		});

		$state.go("photos", new_val, {notify: true});
	}, true);


	$scope.sortColumn = function(column) { 
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state["sort"] = "+" + column;
		return $state.href('photos', new_state);
	};

	$scope.sortOrder = function(order)  { 
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state["sort"] = (order == "asc" ? "+" : "-") + $scope.meta.sort_column;
		return $state.href('photos', new_state);
	}

	$scope.changeLimit = function(limit) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state["limit"] = limit;
		new_state["offset"] = Math.floor($scope.meta.offset / limit) * limit;
		return $state.href('photos', new_state);
	}

	$scope.clearFilters = function() { $scope.state.dirname = "/"; }

	$scope.facet_search = function(facet) {
		//console.log("Generating search function", facet);
		return function(query, callback, extra) {
			var params = JSON.parse(JSON.stringify($stateParams)); // copy
			params.agg = facet
			params.q = query
			angular.forEach(extra, function(val, key) {
				params[key] = val;
			});
			$http.get("/api/photos", {params: params}).success(callback);
		}
	};

	$scope.singleHref = function(photo) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state.id = photo.id;
		return $state.href("photos", new_state);
	}

	$scope.oneliner = function(photo) { return "P#" + photo.id };

	$scope.switchPage = function(offset, limit) {
		console.log("switchPage(", offset, ", ", limit, ")");
		$scope.state.offset = offset;
		$scope.state.limit = limit;
	}

	$scope.movePage = function(offset, limit) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state["offset"] = offset;
		new_state["limit"] = limit;
		return $state.href('photos', new_state);
	}

	$scope.properties = [ 
		["aperture", "Aperture", $filter('aperture'), ],
		["exposure", "Exposure", $filter('exposure'), ],
		["date", "Date", function(v) { return v; }],
		["focal_length", "Focal Length", function(v) { return v; }],
		["focal_length_35", "Focal Length (35mm)", function(v) { return v; }],
		["iso", "ISO", function(v) { return v; }],
		["make", "Make", function(v) { return v; }],
		["model", "Model", function(v) { return v; }],
		["lens", "Lens", function(v) { return v; }],
	];


	//$scope.apertureFormatter = function(v) { return $filter('aperture')(v); }
	//$scope.exposureFormatter = function(v) { return $filter('exposure')(v); }

	$scope.fetch();
}]);

/*
app.controller('PhotoCtrl', ['$scope', '$http', '$stateParams', '$filter', function($scope, $http, $stateParams, $filter) {
	console.log("PhotoCtrl(", $stateParams, ")");	

}]);
*/
