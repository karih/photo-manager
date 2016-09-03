app.controller('PhotosOverviewCtrl', ['$scope', '$http', '$stateParams', '$state', '$document', '$filter', function($scope, $http, $stateParams, $state, $document, $filter) {
	console.log("PhotosOverviewCtrl(" + $stateParams + ")")

	$scope.offset = $stateParams["offset"];
	$scope.limit = $stateParams["limit"];

	this.fetch = function() {
		//console.log("FETCHING ", $stateParams);
		$http.get('/api/photos', {params: $stateParams} ).success(function(data) {
			$scope.photos = data.photos;
			$scope.facets = data.facets;
			$scope.hits = data.results;
		});
	}

	$document.bind('keydown', function(event, args) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		if (event.keyCode == 39 && ($scope.offset + $scope.limit <= $scope.hits)) {
			new_state["offset"] = $scope.offset + $scope.limit;
			$state.go('photos', new_state);
		} else if (event.keyCode == 37) {
			new_state["offset"] = Math.max(0, $scope.offset - $scope.limit);
			$state.go('photos', new_state);
		}	
	});
	$scope.$on('$destroy', function() {
		$document.unbind('keydown');
	});

	this.uiOnParamsChanged = function (changedParams, $transition$) {
		//console.log("CHANGE IN STATE");
		/* state called again with changed parameters */
		angular.forEach(changedParams, function(value, key) {
			$stateParams[key] = value;
			$scope[key] = value;
		})
		this.fetch();
	};

	$scope.movePage = function(offset, limit) {
		var new_state = JSON.parse(JSON.stringify($stateParams));
		new_state["offset"] = offset;
		new_state["limit"] = limit;
		return $state.href('photos', new_state);
	}

	$scope.filter_fun = function(filter) {
		console.log("Generating filter function", filter);
		return function(value) {
			console.log("Moving states for filter ", filter, ". $stateParams: ", $stateParams);
			var new_state = JSON.parse(JSON.stringify($stateParams));
			new_state["offset"] = 0; 
			if (new_state[filter] == value) {
				new_state[filter] = null; // deselect
			} else {
				new_state[filter] = value; // select
			}
			$state.go("photos", new_state);
		}
	}

	$scope.apertureFormatter = function(v) { return "f/" + $filter('number')(v, 1); }
	$scope.exposureFormatter = function(v) { 
		if (v < 1) {
			v = 1 / v;
			return "1/" + $filter('number')(v, 0);
		} else {
			return $filter('number')(v, 1);
		}
	}

	this.fetch();
}]);

app.controller('PhotoCtrl', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {
	console.log("PhotoCtrl(" + $stateParams["id"] + ")");	

	$http.get('/api/photo/' + $stateParams["id"]).success(function(data) {
		$scope.photo = data.photo;
	});
}]);
